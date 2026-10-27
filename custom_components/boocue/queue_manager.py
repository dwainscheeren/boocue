"""Server-owned queues with interruptible gaps and explicit browser ownership."""
import asyncio
from copy import deepcopy
from dataclasses import dataclass,field
import random
import time
import uuid

from .const import RUNTIME_KEYS
from .sequence import QueueCursor


def idle_queue():
    return {'playing':False,'queue_id':None,'run_id':None,'name':None,'waiting':None,'error':None,'step':0,'index':None,'total':0}


@dataclass
class QueueRun:
    definition:dict
    status:dict
    overrides:dict
    context:object
    browser_id:str|None
    automatic_rule:str|None
    plans:list
    task:asyncio.Task|None=None
    advance:asyncio.Event=field(default_factory=asyncio.Event)


class QueueManager:
    def __init__(self,controller):
        self.c=controller
        self.run=None
        self.status=idle_queue()
        self.lock=asyncio.Lock()

    def settings_for(self,definition,effect_id,overrides):
        values={k:deepcopy(self.c.settings[k]) for k in RUNTIME_KEYS}
        values.update(definition['settings'])
        values.update(self.c.settings['effect_routes'].get(effect_id,{}))
        values.update(overrides)
        values['repeat']=False
        return values

    def get_definition(self,qid):
        definition=next((q for q in self.c.settings['queues'] if q['id']==qid),None)
        if not definition:
            raise ValueError('Deze wachtrij bestaat niet')
        return deepcopy(definition)

    def preflight(self,definition,overrides,browser_id):
        requires_browser=False
        plans=[]
        for eid in definition['effects']:
            effect=self.c.effects.get(eid)
            if not effect or effect.category=='moods':
                raise ValueError('Kies losse effecten voor een wachtrij; sfeer speelt op het eigen kanaal')
            settings=self.settings_for(definition,eid,overrides)
            prepared=self.c.prepare_playback(eid,settings,'effect',browser_id)
            self.c.check_audio_overlap('effect',prepared[3],prepared[4],prepared[1])
            plans.append(deepcopy(settings))
            requires_browser |= settings['output']=='browser'
        return requires_browser,plans

    async def start(self,qid,overrides=None,context=None,*,browser_id=None,automatic_rule=None,if_idle=False):
        self.c.ensure_enabled()
        overrides=overrides or {}
        if not isinstance(overrides,dict) or set(overrides)-RUNTIME_KEYS:
            raise ValueError('Onbekende afspeelinstelling')
        definition=self.get_definition(qid)
        browser_id=browser_id or self.c.browser_id
        needs_browser,plans=self.preflight(definition,overrides,browser_id)
        async with self.lock:
            self.c.ensure_enabled()
            if automatic_rule and not self.c.rule_is_armed(automatic_rule):return None
            if if_idle and (self.run or self.c.channels['effect']['playing']):return None
            await self._stop_locked()
            await self.c.async_stop(channel='effect',include_queue=False)
            self.c.ensure_enabled()
            state={**idle_queue(),'playing':True,'queue_id':qid,'run_id':uuid.uuid4().hex,
                   'name':definition['name'],'mode':definition['mode'],'advance':definition['advance'],
                   'repeat':definition['repeat'],'total':len(definition['effects']),'browser_id':browser_id if needs_browser else None}
            run=QueueRun(definition,state,deepcopy(overrides),context,browser_id if needs_browser else None,automatic_rule,plans)
            self.run,self.status=run,state
            run.task=self.c.hass.async_create_task(self._worker(run),'BooCue queue')
            self.c._notify()
            return deepcopy(state)

    async def _stop_locked(self):
        run=self.run
        if not run:return
        # Invalidate first: a delayed worker cannot start an item after Stop.
        self.run=None
        run.status.update(playing=False,waiting=None)
        if run.task and not run.task.done():
            run.task.cancel()
            try:await run.task
            except asyncio.CancelledError:pass
        playing=self.c.channels['effect']
        if playing.get('queue_run_id')==run.status['run_id']:
            await self.c.async_stop(playing.get('run_id'),channel='effect',include_queue=False)
        self.c._notify()

    async def stop(self,expected_run_id=None):
        async with self.lock:
            if expected_run_id and (not self.run or self.run.status['run_id']!=expected_run_id):return
            await self._stop_locked()

    async def next(self,qid=None,context=None,*,automatic_rule=None):
        start=False
        async with self.lock:
            self.c.ensure_enabled()
            run=self.run
            if automatic_rule and not self.c.rule_is_armed(automatic_rule):return None
            if not run:
                if not qid:raise ValueError('Er speelt geen wachtrij')
                start=True
            else:
                if qid and qid!=run.definition['id']:
                    raise ValueError('Er speelt al een andere wachtrij')
                run.advance.set()
                state=self.c.channels['effect']
                if state.get('queue_run_id')==run.status['run_id'] and state['playing']:
                    await self.c.async_stop(state.get('run_id'),channel='effect',include_queue=False)
                return deepcopy(run.status)
        if start:return await self.start(qid,context=context,automatic_rule=automatic_rule,if_idle=bool(automatic_rule))

    async def _wait(self,run):
        if run.advance.is_set():
            run.advance.clear();return
        if run.definition['advance']=='motion':
            run.status.update(waiting='motion',next_at=None)
            self.c._notify()
            await run.advance.wait()
        else:
            gap=random.uniform(run.definition['gap_min'],run.definition['gap_max'])
            run.status.update(waiting='delay',next_at=time.time()+gap)
            self.c._notify()
            try:await asyncio.wait_for(run.advance.wait(),gap)
            except asyncio.TimeoutError:pass
        run.advance.clear()

    async def _worker(self,run):
        cursor=QueueCursor(run.definition['effects'],run.definition['mode'],run.definition['repeat'])
        first=True
        try:
            while self.run is run:
                item=cursor.next()
                if item is None:break
                if not first:await self._wait(run)
                if self.run is not run:break
                index,eid,cycle,step=item
                run.status.update(waiting=None,index=index,effect_id=eid,cycle=cycle,step=step,next_at=None)
                self.c._notify()
                settings=run.plans[index]
                state=await self.c.async_play(eid,settings,run.context,browser_id=run.browser_id,
                    queue_token=run.status['run_id'],if_idle=first and bool(run.automatic_rule))
                if not state:break
                playback=self.c._runs.get('effect')
                if playback and playback.status['run_id']==state['run_id']:
                    await playback.finished.wait()
                if self.c.channels['effect'].get('error'):
                    raise ValueError(self.c.channels['effect']['error'])
                first=False
        except asyncio.CancelledError:raise
        except Exception as err:
            run.status['error']=str(err)[:250]
        finally:
            if self.run is run:
                self.run=None
                run.status.update(playing=False,waiting=None)
                self.c._notify()

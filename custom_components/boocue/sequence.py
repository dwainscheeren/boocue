"""Validated queue definitions and deterministic, duplicate-aware shuffle bags."""
from copy import deepcopy
import random

from .models import number, SAFE_ID


def validate_queues(raw, effect_ids, runtime_validator, runtime_base):
    if not isinstance(raw,list) or len(raw)>30:
        raise ValueError('Kies maximaal 30 wachtrijen')
    result,seen=[],set()
    for item in raw:
        if not isinstance(item,dict) or set(item)-{'id','name','effects','mode','advance','repeat','gap_min','gap_max','settings'}:
            raise ValueError('Ongeldige wachtrij')
        qid,name=item.get('id'),item.get('name','')
        if not isinstance(qid,str) or not SAFE_ID.fullmatch(qid) or qid in seen:
            raise ValueError('Geef elke wachtrij een unieke id')
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:
            raise ValueError('Geef de wachtrij een naam')
        effects=item.get('effects')
        if not isinstance(effects,list) or not 1<=len(effects)<=100 or any(not isinstance(e,str) or e not in effect_ids for e in effects):
            raise ValueError('Kies 1 tot 100 bestaande effecten voor de wachtrij')
        mode,advance,repeat=item.get('mode','sequence'),item.get('advance','auto'),item.get('repeat',True)
        if mode not in {'sequence','random'} or advance not in {'auto','motion'} or not isinstance(repeat,bool):
            raise ValueError('Ongeldige volgorde of voortgang')
        low=number(item.get('gap_min',4),0,3600,'gap_min')
        high=number(item.get('gap_max',15),low,3600,'gap_max')
        settings=item.get('settings',{})
        if not isinstance(settings,dict) or set(settings)-set(runtime_base):
            raise ValueError('Ongeldige wachtrij-instellingen')
        checked=runtime_validator({**runtime_base,**settings})
        # Store only explicit overrides; item-specific audio routes can still take priority.
        settings={k:deepcopy(checked[k]) for k in settings if k!='repeat'}
        result.append({'id':qid,'name':name.strip(),'effects':list(effects),'mode':mode,'advance':advance,
                       'repeat':repeat,'gap_min':low,'gap_max':high,'settings':settings})
        seen.add(qid)
    return result


class QueueCursor:
    """Every row plays once per cycle. Duplicate rows are intentional weighting."""
    def __init__(self,effects,mode='sequence',repeat=False,rng=None):
        self.effects=list(effects)
        self.mode,self.repeat,self.rng=mode,repeat,rng or random.Random()
        self.remaining=[]
        self.cycle=-1
        self.last=None
        self.steps=0

    def next(self):
        if not self.remaining:
            if self.cycle>=0 and not self.repeat:
                return None
            self.cycle+=1
            self.remaining=list(range(len(self.effects)))
        if self.mode=='random':
            candidates=[i for i in self.remaining if self.effects[i]!=self.last] or self.remaining
            index=self.rng.choice(candidates)
        else:
            index=self.remaining[0]
        self.remaining.remove(index)
        self.last=self.effects[index]
        self.steps+=1
        return index,self.last,self.cycle,self.steps

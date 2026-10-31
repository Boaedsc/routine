#!/usr/bin/env python3
"""Messe romaine 1960: calendrier, transferts, précédence et textes propres."""
from __future__ import annotations
import argparse, datetime as dt, json, os, re
from pathlib import Path

PARTS = ['Introitus','Oratio','Lectio','Graduale','Tractus','Alleluia','Evangelium','Offertorium','Secreta','Prefatio','Communio','Postcommunio']
VERSION='Rubrics 1960 - 1960'

def easter(y:int)->dt.date:
    # Computus grégorien de Divinum Officium Date.pm::geteaster.
    G=y%19; C=y//100
    H=(C-C//4-(8*C+13)//25+19*G+15)%30
    I=H-(H//28)*(1-(H//28)*(29//(H+1))*((21-G)//11))
    J=(y+y//4+I+2-C+C//4)%7
    L=I-J; month=3+(L+40)//44; day=L+28-31*(month//4)
    return dt.date(y,month,day)

def dow_sunday0(d:dt.date)->int: return (d.weekday()+1)%7

def advent1(y:int)->dt.date:
    c=dt.date(y,12,25); return c-dt.timedelta(days=dow_sunday0(c)+21)

def getweek(date:dt.date,missa=True)->str:
    """Port fidèle de Date.pm::getweek (tomorrow=False)."""
    y=date.year; doy=date.timetuple().tm_yday; adv=(advent1(y)-dt.date(y,1,1)).days+1
    christmas=dt.date(y,12,25).timetuple().tm_yday
    if doy>=adv:
        if doy<christmas:
            n=(doy-adv)//7+1
            if date.month==11 or date.day<25: return f'Adv{n}'
        return f'Nat{date.day}'
    ordtime=6+7-dow_sunday0(dt.date(y,1,6))
    if date.month==1 and doy<ordtime: return f'Nat{date.day:02d}'
    e=easter(y).timetuple().tm_yday
    if doy<e-63: return f'Epi{(doy-ordtime)//7+1}'
    if doy<e-56:return 'Quadp1'
    if doy<e-49:return 'Quadp2'
    if doy<e-42:return 'Quadp3'
    if doy<e:return f'Quad{(doy-(e-42))//7+1}'
    if doy<e+56:return f'Pasc{(doy-e)//7}'
    n=(doy-(e+49))//7
    if n<23:return f'Pent{n:02d}'
    wdist=((adv-doy)+6)//7
    if wdist<2:return 'Pent24'
    if n==23:return 'Pent23'
    return f'PentEpi{8-wdist}'

def section_parse(path:Path)->dict[str,str]:
    data={}; key=None; buf=[]
    try: lines=path.read_text(encoding='utf-8-sig').splitlines()
    except (OSError,UnicodeError): return data
    def flush():
        if key is not None:data[key]='\n'.join(buf).strip()
    for line in lines:
        m=re.match(r'^\s*\[([\w #,:-]+)\]',line)
        if m:flush();key=m.group(1).strip();buf=[]
        elif key is not None:buf.append(line.rstrip())
        elif line.strip().startswith('@'): data.setdefault('__preamble',line.strip())
    flush();return data

def root_data(root:Path):
    for p in (root/'web/www/missa',root/'missa',root):
        if (p/'Latin').is_dir():return p
    return None

def repo_root(root:Path,data:Path)->Path:
    for p in (root, data.parent.parent, data.parent):
        if (p/'web/www/Tabulae').is_dir():return p
    return root

def find_file(data:Path,lang:str,rel:str)->Path|None:
    rel=rel.replace('\\','/').removesuffix('.txt')+'.txt'
    options=[data/lang/rel]
    if rel.startswith('Commune/'):options += [data.parent/'horas'/lang/rel]
    if lang!='Latin':options += [data/'Latin'/rel]
    if rel.startswith('Commune/'):options += [data.parent/'horas'/'Latin'/rel]
    return next((p for p in options if p.is_file()),None)

def tabular_entries(path:Path,key:str)->list[str]:
    if not path.is_file():return []
    vals=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('#') or '=' not in line:continue
        k,v=line.split('=',1)
        if k==key: vals.append(v.strip())
    return vals

def table_config(tab:Path,version=VERSION):
    """Lire la configuration Directorium; si aucune data.txt n'est fournie, utiliser les tables uploadées 1960."""
    cfgfile=tab/'data.txt'
    if cfgfile.is_file():
        rows=[x.split(',') for x in cfgfile.read_text(encoding='utf-8-sig').splitlines() if x and not x.startswith('#')]
        for r in rows:
            if r[0]==version:
                return {'calendar':r[1],'transfer':r[2],'stransfer':r[3], 'base':r[4] if len(r)>4 else '', 'tbase':r[5] if len(r)>5 else ''}
        raise ValueError(f'Version absente de Tabulae/data.txt: {version}')
    if version in (VERSION,'1960','Rubrics 1960 - 2020 USA'):
        return {'calendar':'','transfer':'1960','stransfer':'1960','base':'','tbase':''}
    return {'calendar':'','transfer':version,'stransfer':version,'base':'','tbase':''}

def load_kalendaria(tab: Path, version=VERSION) -> dict:
    """Charge tab/Kalendaria/<calendar>.txt en dict {'MM-DD': {champs}}."""
    cfg = table_config(tab, version)
    name = cfg.get('calendar') or ''
    if not name:
        return {}
    p = tab / 'Kalendaria' / f'{name}.txt'
    if not p.is_file():
        return {}
    out = {}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if not line or line.startswith('#') or '=' not in line:
            continue
        raw, _, _tags = line.partition(';;')
        key, val = raw.split('=', 1)
        out[key.strip()] = {'valeur': val.strip()}
    return out

def effective_calendar(tab, mmdd):
    """Renvoie (valeurs, source) du calendrier effectif pour une date MM-DD."""
    if tab and mmdd in tab:
        return tab[mmdd], mmdd
    general = (tab or {}).get('general') or (tab or {}).get('Generale')
    if general is not None:
        return general, 'general'
    return {}, None

def transfer_tables(tab:Path,kind:str)->list[Path]:
    """Préférence au dossier Tabulae de la racine, puis tables de secours uploadées."""
    if (tab/kind).is_dir(): return [tab/kind]
    upload=Path(__file__).resolve().parent.parent/'uploads'
    return [upload] if kind=='Transfer' and upload.is_dir() else []

def _table_lines(dirs:list[Path],name:str)->list[str]:
    for directory in dirs:
        p=directory/(name+'.txt')
        if p.is_file(): return p.read_text(encoding='utf-8-sig').splitlines()
    return []

def _tag_matches(tags:str,tag:str)->bool:
    return not tags.strip() or re.search(r'\b'+re.escape(tag)+r'\b',tags) is not None

def _filter_transfer_line(line:str,filter_no:int)->bool:
    # Directorium.pm::load_transfer_file, exact Jan/Feb leap-year filters.
    rx1=r'^(?:Hy|seant)?(?:01|02-[01]|02-2[01239]|dirge1)'
    rx2=r'^(?:Hy|seant)?(?:01|02-[01]|02-2[01239]|.*=(01|02-[01]|02-2[0123])|dirge1)'
    return not re.search(rx2,line) if filter_no==1 else bool(re.search(rx1,line)) if filter_no==2 else True

def _mapped_entries(value:str)->list[str]:
    return [v.strip() for v in value.split('~') if v.strip()]

def _annual_map(tab:Path,date:dt.date,version:str,kind:str)->tuple[dict[str,str],str|None]:
    """Port de load_transfers: lettre dominicale, date de Pâques, lignes bis et filtres bissextiles."""
    eas=easter(date.year); easterkey=eas.month*100+eas.day
    letter=(easterkey-319+(1 if eas.month==4 else 0))%7
    letters='abcdefg'; leap=date.year%4==0 and (date.year%100!=0 or date.year%400==0)
    names=[letters[letter],str(easterkey)]
    if leap:
        next_easter=easterkey+1
        if next_easter==332: next_easter=401
        names += [str(easterkey)+'bis',letters[(letter-6)%7],str(next_easter)]
    dirs=transfer_tables(tab,kind); cfg=table_config(tab,version); tag=cfg[kind.lower()]
    merged={}
    for i,name in enumerate(names):
        filt=2 if leap and i>=3 else (1 if leap and i<2 else 0)
        for line in _table_lines(dirs,name):
            if not line or line.startswith('#') or not _filter_transfer_line(line,filt): continue
            raw,sep,tags=line.partition(';;')
            if sep and not _tag_matches(tags,tag): continue
            if '=' in raw:
                key,val=raw.split('=',1); merged[key]=val
    return merged,tag

def annual_transfer(tab:Path,date:dt.date,version=VERSION,kind='Transfer')->tuple[list[str],str|None]:
    """Retourne la valeur de la date après héritage tbase (Directorium::get_from_directorium)."""
    seen=set(); current=version
    while current and current not in seen:
        seen.add(current)
        mapping,tag=_annual_map(tab,date,current,kind)
        key=f'{date.month:02d}-{date.day:02d}'
        if mapping.get(key): return [mapping[key]],tag
        cfg=table_config(tab,current); current=cfg.get('tbase','')
    return [],None

def rank_info(sections:dict[str,str])->tuple[float,str,str]:
    """Pick [Rank] entry explicitly marked for 1960 where present."""
    raw=sections.get('Rank',''); lines=raw.splitlines(); found=[]; i=0
    while i<len(lines):
        m=re.search(r';;([^;]*);;\s*([0-9]+(?:\.[0-9]+)?)',lines[i])
        if m:
            cond=''
            if i+1<len(lines) and re.match(r'\s*\(sed rubrica',lines[i+1],re.I):cond=lines[i+1].lower()
            found.append((float(m.group(2)),m.group(1).strip(),lines[i].split(';;')[-1].strip(),cond))
        i+=1
    for r in found:
        if 'rubrica 1960' in r[3] or 'rubrica 196' in r[3]:return r[0],r[1],r[2]
    for r in found:
        if not r[3] or not re.search(r'rubrica\s+(?:1570|1888|1906|1930)',r[3]):return r[0],r[1],r[2]
    return (found[0][0],found[0][1],found[0][2]) if found else (0,'','')

def expand(text:str,data:Path,lang:str,source:Path,sec:str,seen=frozenset(),depth=0)->tuple[str,list[dict]]:
    if depth>12:return '',[]
    refs=[]
    pat=re.compile(r'^\s*@([^\s:]+)?(?::([^\s:]+))?(?::([^\n]*))?\s*$',re.M)
    def sub(m):
        target=m.group(1); targetsec=m.group(2) or sec
        p=source if not target else find_file(data,lang,target)
        if p is None and target: p=find_file(data,'Latin',target)
        if p is None or (str(p),targetsec) in seen:
            refs.append({'fichier':target,'section':targetsec,'resolu':False});return ''
        doc=section_parse(p); val=doc.get(targetsec,'')
        if not val:
            refs.append({'fichier':str(p),'section':targetsec,'resolu':False});return ''
        expanded,nested=expand(val,data,lang,p,targetsec,seen|{(str(p),targetsec)},depth+1)
        refs.append({'fichier':str(p),'section':targetsec,'resolu':True,'sous_references':nested or None})
        return expanded
    out=pat.sub(sub,text)
    return out.strip(),refs

def inherited_section(path:Path,key:str,data:Path,lang='Latin',seen=frozenset(),depth=0)->str:
    """Résoudre une section via le préambule de fichier @Chemin (héritage SetupString)."""
    if depth>12 or (str(path),key) in seen:return ''
    doc=section_parse(path); value=doc.get(key,'')
    if value.strip():return value
    pre=doc.get('__preamble','')
    m=re.match(r'^@([^\s:]+)?(?::([^\s:]+))?',pre) if pre else None
    if not m:return ''
    target=m.group(1); targetsec=m.group(2) or key
    p=path if not target else find_file(data,lang,target)
    if p is None and target:p=find_file(data,'Latin',target)
    return inherited_section(p,targetsec,data,lang,seen|{(str(path),key)},depth+1) if p else ''

def inherited_document(path:Path|None,data:Path,lang='Latin')->dict[str,str]:
    if not path:return {}
    doc=section_parse(path)
    for key in PARTS+['Rank','Rule','Prefatio']:
        if not doc.get(key):
            val=inherited_section(path,key,data,lang)
            if val:doc[key]=val
    return doc

def _permanent_map(tab:Path,date:dt.date,version=VERSION)->tuple[dict[str,str],str|None]:
    """Lecture fixe Directorium::load_tempora(Generale) et inheritance via base."""
    current=version; seen=set(); merged={}; firsttag=None
    while current and current not in seen:
        seen.add(current); cfg=table_config(tab,current); p=tab/'Tempora'/'Generale.txt'; local={}
        if p.is_file():
            for line in p.read_text(encoding='utf-8-sig').splitlines():
                if not line or line.startswith('#') or '=' not in line:continue
                raw,sep,tags=line.partition(';;'); key,val=raw.split('=',1)
                if sep and not _tag_matches(tags,cfg.get('transfer','')):continue
                m=re.search(r'::([a-g])',val)
                if m:
                    eas=easter(date.year); ek=eas.month*100+eas.day; li=(ek-319+(1 if eas.month==4 else 0))%7
                    leap=date.year%4==0 and (date.year%100!=0 or date.year%400==0)
                    expected='abcdefg'[(li-6)%7] if leap and (key.startswith('01-') or key.startswith('02-01') or re.match(r'02-2[01239]',key)) else 'abcdefg'[li]
                    if m.group(1)!=expected:continue
                    val=val.replace(m.group(0),'')
                local[key]=val
        for k,v in local.items():merged.setdefault(k,v)
        if firsttag is None:firsttag=cfg.get('transfer')
        current=cfg.get('tbase','')
    return merged,firsttag

def permanent_day_transfer(tab:Path,date:dt.date,version=VERSION)->tuple[list[str],str|None]:
    mapping,tag=_permanent_map(tab,date,version)
    return (_mapped_entries(mapping.get(f'{date.month:02d}-{date.day:02d}','')),tag)

def seasonal_transfer(tab:Path,date:dt.date,key:str,version=VERSION)->tuple[list[str],str|None]:
    annual,tag=_annual_map(tab,date,version,'Transfer')
    permanent,ptag=_permanent_map(tab,date,version)
    val=annual.get(key) or permanent.get(key)
    return (_mapped_entries(val) if val else [],tag if annual.get(key) else ptag)

def _is_transferred_away(tab:Path,date:dt.date,office:str,version=VERSION)->bool:
    """Partiel fidèle à Directorium::transfered pour les données générales accessibles."""
    if not office:return False
    plain=re.sub(r'^Sancti(?:M|Cist|OP)?/','',office,flags=re.I)
    annual, _=_annual_map(tab,date,version,'Transfer')
    permanent,_=_permanent_map(tab,date,version)
    for mapping in (annual,permanent):
        for key,val in mapping.items():
            if not val or re.search(r'(?:dirge|Hy)',key,re.I):continue
            if re.search(r'Tempora',val,re.I) and not re.search(r'Epi1-0',val,re.I):continue
            if re.search(r'v\s*$',val,re.I):continue
            if plain.lower() in val.lower():return True
    return False

def messes_sanctoral(data:Path,date:dt.date)->list[str]:
    """Liste des fichiers Sancti pour la date : variantes MM-DDmN triées si présentes, sinon fichier de base."""
    base=f'{date.month:02d}-{date.day:02d}'
    dossier=data/'Latin'/'Sancti'
    if not dossier.is_dir():return []
    variantes=sorted(
        (p.stem for p in dossier.glob(f'{base}m*.txt') if re.fullmatch(rf'{base}m\d+',p.stem)),
        key=lambda s:int(s.rsplit('m',1)[1])
    )
    if variantes:return [f'Sancti/{v}' for v in variantes]
    return [f'Sancti/{base}'] if (dossier/f'{base}.txt').is_file() else []

def _une_messe(date:dt.date,data:Path,tab:Path,saint:str|None)->dict:
    """Calcule l'occurrence et les sections pour une messe donnée (saint = fichier sanctoral ou None)."""
    week=getweek(date)
    dow=dow_sunday0(date)
    temporal=f'Tempora/{week}'+(f'-{dow}' if not week.startswith('Nat') else '')
    tp=find_file(data,'Latin',temporal)
    if not tp and temporal.endswith('-0'):tp=find_file(data,'Latin',temporal+'a')
    season_dest,season_table=seasonal_transfer(tab,date,temporal)
    if season_dest and season_dest[0].lower().startswith('tempora/'):
        redirected=find_file(data,'Latin',season_dest[0])
        if redirected:tp=redirected;temporal=season_dest[0]
    kalendaria=load_kalendaria(tab)
    calvals_dict,cal_used=effective_calendar(kalendaria,f'{date.month:02d}-{date.day:02d}')
    calvals=calvals_dict.get('valeur','').split('|') if calvals_dict else []
    transfer_vals,transfer_table=annual_transfer(tab,date)
    permanent_vals,permanent_table=permanent_day_transfer(tab,date)
    temp_override=''
    selected_transfer=transfer_vals or permanent_vals
    if selected_transfer and selected_transfer[0].lower().startswith('tempora/'):
        temp_override=selected_transfer[0]
        tp=find_file(data,'Latin',temp_override)
        if not tp: tp=find_file(data,'Latin','Tempora/'+temp_override.split('/',1)[-1])
    entries=calvals[:]
    if transfer_vals and not transfer_vals[0].lower().startswith('tempora/'):
        entries=_mapped_entries(transfer_vals[0])
    elif permanent_vals and not permanent_vals[0].lower().startswith('tempora/'):
        entries=permanent_vals
    entry=entries[0] if entries else ''
    names=entry.split('=')
    office=names[0] if names and names[0] not in ('XXXXX','---','X-X','XX-XX') else ''
    if entry.upper() in ('X-X','XX-XX'):entries=[]
    commem=[]
    for val in entries:
        f=val.split('=');commem.extend([x for x in f[4:] if x and not x.isdigit()])
    # Le sanctoral est désormais fourni par l'appelant (main_mass), qui énumère les variantes mN.
    if saint and _is_transferred_away(tab,date,saint):saint=None
    sp=find_file(data,'Latin',saint) if saint else None
    ts=inherited_document(tp,data) if tp else {}; ss=inherited_document(sp,data) if sp else {}
    tr,_,_=rank_info(ts); sr,_,_=rank_info(ss)
    twinner=False
    if ss:
        if not ts:twinner=True
        elif 'Conceptione Immaculata' in ss.get('Rank','') and 'rubrica 1960' in ss.get('Rank','').lower():twinner=True
        elif sr>tr:twinner=True
        elif sr==tr and sr>0 and dow!=0:twinner=True
        elif dow==0 and sr>=6 and tr<=5:twinner=True
    winner=saint if twinner else temporal
    wp=sp if twinner else tp; win=ss if twinner else ts
    if not win and ss:winner=saint;wp=sp;win=ss;twinner=True
    scripture_path=tp if tp and (twinner and ts.get('Lectio')) else wp
    scripture_transfer,scripture_table=annual_transfer(tab,date,kind='Stransfer')
    if scripture_transfer:
        st=scripture_transfer[0]
        rel=st if '/' in st else f'Tempora/{st}'
        scripture_path=find_file(data,'Latin',rel) or find_file(data,'Latin',f'Tempora/{st}') or scripture_path
    commref=''
    _,_,rankcommon=rank_info(win)
    m=re.search(r'(?:ex|vide)\s*(C\d+[a-z]*)',rankcommon,re.I)
    if m:commref='Commune/'+m.group(1)
    rule=win.get('Rule','')
    m2=re.search(r'(?:^|\n)\s*(?:ex|vide)\s*(C\d+[a-z]*)',rule,re.I)
    if m2 and not commref:commref='Commune/'+m2.group(1)
    results={}
    for lang in ('Latin','Francais'):
        results[lang]={}
        for part in PARTS:
            source=scripture_path if part in ('Lectio','Evangelium') else wp
            base=inherited_document(source,data,lang) if source else {}
            key=part
            if part in ('Tractus','Alleluia'):
                raw=base.get('Graduale','')
                marker='!'+part
                if marker in raw:
                    chunks=re.split(r'(?m)^!'+part+r'\s*$',raw,maxsplit=1)
                    txt=chunks[-1].strip()
                    if part=='Tractus':txt=re.split(r'(?m)^!(?:Alleluia)\s*$',txt)[0].strip()
                    else:txt=re.split(r'(?m)^!(?:Tractus)\s*$',txt)[0].strip()
                    key='Graduale'
                    direct=txt
                else:
                    direct=base.get(part,''); key=part
            else:direct=base.get(key,'')
            chosen=source
            chosenlangfile=find_file(data,lang,chosen.relative_to(data/'Latin').as_posix()) if chosen and chosen.is_relative_to(data/'Latin') else None
            candidates=[(chosenlangfile,key,direct)]
            if commref and part in ('Introitus','Oratio','Lectio','Graduale','Tractus','Alleluia','Offertorium','Secreta','Communio','Postcommunio'):
                cp=find_file(data,lang,commref); candidates.append((cp,part,''))
            alt=tp if chosen!=tp else None
            if alt:candidates.append((find_file(data,lang,alt.relative_to(data/'Latin').as_posix()),part,''))
            selected=None;txt='';refs=[]
            for p,k,val in candidates:
                if val and p and p.is_file(): selected=p;txt=val;key=k;break
                if p:
                    v=inherited_section(p,k,data,lang)
                    if v:selected=p;txt=v;key=k;break
            if selected:
                txt,refs=expand(txt,data,lang,selected,key)
            if not txt and lang=='Francais':
                p=find_file(data,'Latin',chosen.relative_to(data/'Latin').as_posix()) if chosen and chosen.is_relative_to(data/'Latin') else None
                val=inherited_section(p,key,data,'Latin') if p else ''
                if not val and commref:
                    p=find_file(data,'Latin',commref);val=inherited_section(p,part,data,'Latin') if p else ''
                if val and p:txt,refs=expand(val,data,'Latin',p,key);selected=p
            if selected and selected.is_relative_to(data):
                rel=selected.relative_to(data).as_posix()
            elif selected and selected.is_relative_to(data.parent/'horas'):
                rel='../horas/'+selected.relative_to(data.parent/'horas').as_posix()
            elif chosenlangfile:
                rel=chosenlangfile.relative_to(data).as_posix()
            elif source:
                rel=source.relative_to(data).as_posix()
            else:
                rel=None
            results[lang][part]={'fichier':rel,'section':key,'texte':txt,'references':refs or None}
    used=sorted({x['fichier'] for ll in results.values() for x in ll.values() if x['fichier']})
    out={'occurrence':{
            'gagnant':winner,
            'nom_sanctoral':names[1] if len(names)>1 else '',
            'classe':rank_info(win)[0],
            'commemorations':commem,
            'fichier_gagnant':wp.relative_to(data).as_posix() if wp else None,
            'temporal':tp.relative_to(data).as_posix() if tp else None,
            'sanctoral':sp.relative_to(data).as_posix() if sp else None,
            'calendrier':cal_used,
            'table_transfert':transfer_table,
            'transfert_annuel':transfer_vals,
            'transfert_permanent':permanent_vals,
            'table_transfert_permanent':permanent_table,
            'transfert_saisonnier':season_dest,
            'table_transfert_saisonnier':season_table,
            'transfert_scriptura_annuel':scripture_transfer,
            'table_transfert_scriptura':scripture_table,
            'note':'Sélection d’occurrence portée à partir des tables et rangs; limites rubricales restantes décrites dans STRUCTURE.md'},
         'sections':results,
         'fichiers_utilises':used}
    out['sections_vides']=sum(not item['texte'].strip() for ll in results.values() for item in ll.values())
    return out

def main_mass(date:dt.date,root:Path)->dict:
    data=root_data(root)
    if data is None:raise FileNotFoundError(f'Données missa introuvables sous {root}')
    tab=repo_root(root,data)/'web/www/Tabulae'
    candidats=messes_sanctoral(data,date) or [None]
    messes=[]
    for i,saint in enumerate(candidats,start=1):
        m=_une_messe(date,data,tab,saint)
        m['numero']=i
        messes.append(m)
    return {
        'date':date.isoformat(),
        'rubriques':VERSION,
        'semaine':getweek(date),
        'paques':easter(date.year).isoformat(),
        'nombre_messes':len(messes),
        'messes':messes,
    }

def cli():
    p=argparse.ArgumentParser(description='Résolution des propres de la messe romaine 1960')
    p.add_argument('date',help='AAAA-MM-JJ')
    p.add_argument('--racine',default=os.environ.get('DIVINUM_OFFICIUM_ROOT','.'),help='racine du dépôt Divinum Officium ou dossier web/www/missa')
    p.add_argument('--messe',type=int,default=None,help='numéro de la messe (1, 2, 3…) ; par défaut toutes les messes du jour')
    p.add_argument('--json',action='store_true',help='sortie JSON détaillée')
    p.add_argument('--fichiers',action='store_true',help='sortie compacte des fichiers/sections')
    a=p.parse_args()
    try:d=dt.date.fromisoformat(a.date)
    except ValueError:p.error('date invalide, format attendu AAAA-MM-JJ')
    out=main_mass(d,Path(a.racine).expanduser().resolve())
    if a.messe is not None:
        if not 1<=a.messe<=out['nombre_messes']:
            p.error(f"cette date compte {out['nombre_messes']} messe(s)")
        out={**{k:v for k,v in out.items() if k!='messes'},'messes':[out['messes'][a.messe-1]],'nombre_messes':out['nombre_messes']}
    if a.fichiers:
        for m in out['messes']:
            m['sections']={l:{s:{'fichier':v['fichier'],'section':v['section']} for s,v in sec.items()} for l,sec in m['sections'].items()}
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':cli()
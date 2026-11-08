from routine.gabc_engine import rendre_gabc

gabc = r"""(f3) AL(e)le(f)lú(hi~){ia}.(i_[oh:h]h/iggf.0) <clear>*(,) <i>ij.</i>(hv.iji./[-0.5]ef/h_f//hv.ghe/hhh.f!gwhf.1) (::) <sp>V/</sp>. Tu(hi) es(i) Pe(jiihi)trus,(iv.hh/fgf.) (;) et(f) su(fg)per(f) hanc(f) pe(f!hh/ijHF'ivH'GEf./hfhhf/ge)tram(e.) (:) ae(f)di(e)fi(f)cá(ffe/ffe/fc..)(,)(ef!hvvF'Ehhh)bo(ivH'Ghf..) (;) Ec(f)clé(hh)si(h)am(hi~) *() me(i_[oh:h]h/jij)am.(jvvIH'GE//f!gwhf.1) (::)"""

print(rendre_gabc(gabc, nom="Tu es Petrus", dossier="partitions"))
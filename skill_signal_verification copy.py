import pandas as pd, numpy as np, re
U='/mnt/user-data/uploads/'
V={}
g=pd.read_csv(U+'GTTC_Shortterm_Courses.csv')
yrs=['2018-19','2019-20','2020-21','2021-22']
g['CoE']=g['Centre of Excellence'].ffill()
tr=g[g['Sl.No'].astype(str)=='Total'].iloc[0]
d=g[g['Sl.No'].astype(str).str.isnumeric()].copy()
for y in yrs+['Total']: d[y]=pd.to_numeric(d[y])
V['gttc_tot']={y:int(d[y].sum()) for y in yrs}
assert V['gttc_tot']=={y:int(tr[y]) for y in yrs}=={'2018-19':1040,'2019-20':2515,'2020-21':2086,'2021-22':2420}
V['gttc_grand']=int(d['Total'].sum()); assert V['gttc_grand']==int(tr['Total'])==8061
assert ((d[yrs].sum(axis=1)-d['Total']).abs().max())==0
V['centres']=d[['Centre Name','CoE','Total']+yrs].copy()
V['n_reporting']={y:int(d[y].notna().sum()) for y in yrs}
V['filled']=int(d[yrs].notna().sum().sum()); V['cells']=int(d[yrs].size)
lfl=d[d[yrs].notna().all(axis=1)]
V['lfl_names']=lfl['Centre Name'].tolist(); V['lfl']={y:int(lfl[y].sum()) for y in yrs}
t=V['gttc_tot']; V['yoy']=[(t[yrs[i]]-t[yrs[i-1]])/t[yrs[i-1]]*100 for i in range(1,4)]
l=V['lfl']; V['lfl_yoy']=[(l[yrs[i]]-l[yrs[i-1]])/l[yrs[i-1]]*100 for i in range(1,4)]
V['partner']=d.groupby('CoE')['Total'].sum().to_dict()
V['mysuru_share']=d.loc[d['Centre Name']=='Mysuru','Total'].iloc[0]/8061*100
top2=d.sort_values('Total',ascending=False)['Total'].head(2).sum(); V['top2_share']=top2/8061*100
V['siemens_share']=[v for k,v in V['partner'].items() if 'Siemens' in k][0]/8061*100
# passed file
p=pd.read_csv(U+'GTTC_Number_of_Students_Passed_2019-2021_0.csv',keep_default_na=False)
coe=p[p['INFORMATION TYPE'].str.contains('COE')].iloc[0]
V['passed_coe']=[int(coe[c]) for c in p.columns[2:5]]
assert V['passed_coe']==[t['2019-20'],t['2020-21'],t['2021-22']]
st=p[p['INFORMATION TYPE']=='SHORT TERM COURSE'].iloc[0]; V['passed_short']=[int(st[c]) for c in p.columns[2:5]]
# census
c=pd.read_csv(U+'census_2011_ddw_b06_2900_2011.csv'); c['Area Name']=c['Area Name'].str.strip()
cat=[x for x in c.columns if x.startswith('Industrial Category') and x.endswith('Persons')]
c['ind']=c[cat].sum(axis=1)
k=c[(c['Area Name']=='State - Karnataka')&(c['Total/Rural/Urban']=='Total')&(c['Age-Group']=='Total')].iloc[0]
V['census_total']=int(k.ind); assert V['census_total']==4473682
agri=sum(k[x] for x in cat if ' - A - ' in x); V['agri_share']=agri/k.ind*100
V['fem_share']=sum(k[x.replace('Persons','Females')] for x in cat)/k.ind*100
V['n_dist_census']=int(((c['Area Name'].str.startswith('District'))&(c['Total/Rural/Urban']=='Total')&(c['Age-Group']=='Total')).sum())
# enrolment
e=pd.read_csv(U+'TotalEnrollmentbyLevel_2020-21.csv'); e.columns=[x.strip() for x in e.columns]
am=e[e['Management'].str.contains('All Management')]; V['n_edu_dist']=len(am)-1
# SLSWCC
s=pd.read_csv(U+'State_Level_Single_Window_Committee_Industrydetails_2021.csv',encoding='cp1252'); s.columns=[x.replace('\n',' ').strip() for x in s.columns]
V['slswcc_n']=len(s); V['slswcc_emp']=int(s['EMPLOYMENT'].sum()); V['slswcc_inv']=float(s['INVESTMENT (Rs. In Crores)'].sum()); V['slswcc_zero']=int((s['EMPLOYMENT']==0).sum())
V['slswcc_raw_sectors']=s['SECTOR'].nunique(); V['slswcc_sectors']=s['SECTOR'].str.strip().str.upper().nunique()
def dist(x):
    m=re.search(r'([A-Za-z\. ]+?)\s+Dist',str(x)); return m.group(1).strip() if m else None
V['slswcc_dist_parsed']=int(s['LOCATION'].map(dist).notna().sum())
if __name__=='__main__':
    import pprint; V2={k:v for k,v in V.items() if k!='centres'}; pprint.pprint(V2); print(V['centres'])

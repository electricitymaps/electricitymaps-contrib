import json, pygrib, gzip
with pygrib.open('flxf2016061000.01.2016061000.grb2') as f:
    grb = f.select(name='Downward long-wave radiation flux', level=0)[0]
    # obj = {
    #     'lonlats': [],
    #     'DLWRF': []
    # }
    # for i in range(grb['Nj']):
    #     for j in range(grb['Ni']):
    #         n = i*grb['Ni'] + j
    #         obj['lonlats'].append([grb['longitudes'][n], grb['latitudes'][n]])
    #         obj['DLWRF'].append(grb['values'][i, j])
    obj = {
        'lonlats': [grb['longitudes'].tolist(), grb['latitudes'].tolist()],
        'values': grb['values'].tolist()
    }

with gzip.open('backend/data/solar.json.gz', 'w') as f:
    json.dump(obj, f)

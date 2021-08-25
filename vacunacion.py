#! /usr/bin/env python3

# to get these libraries: pip3 install astropy numpy 
from astropy import table
import numpy as np

# to make plots: pip3 install matplotlib 
def vacunas_adquiridas(plot=False, show=True):

    name = 'vacunas_importadas_fabricante_fecha'

    tab = table.Table.read(f'input/{name}.csv')

    print('Quick check of table consistency')
    MSG = 'el núm de vacunas {lab} ({total}) difiere de lo reportado ({dec})'
    for lab in np.unique(tab['laboratorio']):
        carg = tab[tab['laboratorio'] == lab]
        total_dec = int(carg[-1]['total_laboratorio_reportado'])
        total = carg['cantidad'].sum()
        dif = ' (conforme a lo declarado)'
        if total_dec != total:
            dif = ' (difiere de los {total_dec:11,} declarados)'
        print(f'total {lab:12}{total:11,}{dif}')

    total_dec = int(tab[-1]['total_reportado'])
    total = tab['cantidad'].sum()
    dif = ' (conforme a lo declarado)'
    if total_dec != total:
        dif = ' (difiere de los {total_dec:11,} declarados)'
    print('-' * 29)
    print(f'total {"":12}{total:11,}{dif}')

    tab.remove_columns(['total_laboratorio_reportado', 'total_reportado'])
    tab.write(f'output/contrib/{name}.csv', overwrite=True)
    
    if plot:

        from matplotlib import pylab as plt

        fig = plt.figure(3)
        fig.clf()
        ax = fig.add_subplot(111)

        fecha = [np.datetime64(f) for f in tab['fecha']]
        cantidad = tab['cantidad'] / 1e6
        previo = np.zeros_like(cantidad)
        
        for lab in np.unique(tab['laboratorio']):
            q = cantidad * (tab['laboratorio'] == lab)
            total  = q.cumsum()
            ax.fill_between(fecha, previo + total, previo, step="pre",
                label=lab, alpha=0.5)
            ax.plot(fecha, previo + total, drawstyle="steps")
            previo += total
       
        ax.set_ylabel('millones de dosis')
        ax.set_xlabel('fecha')

        xticks = [np.datetime64(f"20{y}-{m:02}-01") for y in range(20,23) 
                        for m in range(1,13)]
        xticks = [t for t in xticks if t > fecha[0] and t < fecha[-1]]
        xticklabels = [f"{str(f)[8:10]}/{str(f)[5:7]}" for f in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=60)
        ax.set_ylim(0, ax.get_ylim()[1])
        ax.set_xlim(min(fecha), max(fecha))
        ax.grid(axis='both')

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(reversed(handles), reversed(labels), loc='upper left')
        
        fig.tight_layout()
        if show:
            fig.show()
        fig.savefig(f'output/contrib/{name}.pdf')

    

def get_minciencias_table(num, name, max_time=7200):
    """Cached download from MinCiencias's github"""

    import os
    import sys
    import time

    GITHUB = 'https://raw.githubusercontent.com'
    MINCIENCIAS_URL = f'{GITHUB}/MinCiencia/Datos-COVID19'
   
    name = f"producto{num}/{name}.csv" 
    os.makedirs(os.path.split(name)[0], exist_ok=True)
    now = time.time()
    
    try:
        cached = os.path.exists(name) and now-os.stat(name).st_mtime < max_time
        print(os.path.exists(name))
        print(now, os.stat(name).st_mtime, max_time)
    except:
        cached = False # if os.stat doesn't work on your OS
 
    url = name if cached else f"{MINCIENCIAS_URL}/master/output/{name}"

    try:
        tab = table.Table.read(url, format='ascii.csv')
    except FileNotFoundError as e:
        print('error downloading table: ', e)
        sys.exit(1)
    finally:
        for name in tab.colnames[1:]:
            tab[name].fill_value = 0
        tab = tab.filled()
 
    if not cached:
        print(cached)
        tab.write(name, format='ascii.csv', overwrite=True)

    return tab

def total_vacunados():
    
    dosis = ('primera dosis', 'segunda dosis', 'única dosis',
             'vacunación iniciada', 'vacunación completada',
             'inmunización') 

    vac = [get_minciencias_table(78, f'vacunados_edad_fecha_{dosis}Dosis')
                        for dosis in ('1era', '2da', 'Unica')]

    fecha = vac[0].colnames[1:]
    edad = vac[0]['Edad']
    vac = np.array([[np.array(v[f], dtype=int) for f in fecha] for v in vac])
    vac = vac.cumsum(axis=1)

    # missing age rows will be inserted; centenarians are gathered
    cero = np.zeros_like(vac[...,0])
    cent = vac[..., edad >= 100].sum(axis=2)
    vac = [vac[..., e==edad][...,0] if e in edad else cero for e in range(101)]
    vac = np.moveaxis(vac, 0, 2)
    vac[...,-1] = cent 
    edad = list(range(101))

    iniciado = vac[0] + vac[2]
    terminado = vac[1] + vac[2]

    inmunizado = np.zeros_like(iniciado)
    inmunizado[14:] = vac[1,:-14]
    inmunizado[28:] += vac[2,:-28]

    vac = np.array([*vac, iniciado, terminado, inmunizado])
    
    return (dosis, fecha, edad), vac 

def avance_edad(plot=False, show=True):
    
    import os
    os.makedirs('output/contrib', exist_ok=True)

    (dosis, _, edad), vacunados = total_vacunados() 
    avance = vacunados[:,-1,:]
    
    names = ['fecha', *dosis]
    cols = [edad, *avance]
    tab = table.Table(cols, names=names)
    
    tab.write('output/contrib/total_vacunados_edad.csv', 
                        overwrite=True, format='ascii.csv')
    
    pop = table.Table.read("poblacion.dat", format='ascii.fixed_width_two_line')
    pop = [pop['población'][pop['edad'] == e][0] for e in edad]
  
    avance = 100 * avance / pop 
    cols = [edad, *avance] 
    tab = table.Table(cols, names=names)
    tab.write('output/contrib/fraccion_vacunados_edad.csv',
                        overwrite=True, format='ascii.csv')
    
    if plot:

        from matplotlib import pylab as plt

        fig = plt.figure(2)
        fig.clf()
        ax = fig.add_subplot(111)
        
        for name, fmt in zip(tab.colnames[-3:], ('k-', 'm-', 'g-')):
            ax.plot(edad, tab[name], fmt, label=name)

        ax.set_ylabel('% del grupo etario')
        ax.set_xlabel('edad')
        ax.set_ylim(0,100)

        xticks = range(0, 101, 10)
        ax.set_xticks(xticks)
        
        yticks = list(range(0,101,10))
        yticklabels = [str(yt) if not yt % 20 else '' for yt in yticks]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        ax.grid(axis='both')

        ax.legend(loc='lower right')
        
        fig.tight_layout()
        if show:
            fig.show()
        fig.savefig('output/contrib/fraccion_vacunados_edad.pdf')


def avance_fecha(plot=False, show=True):

    import os
    os.makedirs('output/contrib', exist_ok=True)
    
    (dosis, fecha, _), vacunados = total_vacunados()
    avance = vacunados.sum(axis=2)

    names = ['fecha', *dosis]
    cols = [fecha, *avance]
    tab = table.Table(cols, names=names)


    tab.write('output/contrib/total_vacunados_fecha.csv', 
                        overwrite=True, format='ascii.csv')

    pop = table.Table.read("poblacion.dat", format='ascii.fixed_width_two_line')
    pop = pop['población'].sum()
   
    avance = 100 * avance / pop 
    cols = [fecha, *avance]
    tab = table.Table(cols, names=names)
    
    tab.write('output/contrib/fraccion_vacunados_edad.csv', 
                        overwrite=True, format='ascii.csv')
    
    if plot:

        from matplotlib import pylab as plt

        fig = plt.figure(1)
        fig.clf()
        ax = fig.add_subplot(111)
        
        for name, fmt in zip(tab.colnames[-3:], ('k-', 'm-', 'g-')):
            ax.plot(fecha, tab[name], fmt, label=name)

        ax.set_ylabel('% de la población')
        ax.set_xlabel('fecha')
        ax.set_ylim(0,100)

        xticks = [f for f in fecha if f.endswith('01') or f.endswith('16')]
        xticklabels = [f"{f[8:10]}/{f[5:7]}" for f in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=60)

        yticks = list(range(0,110,10))
        yticklabels = [str(yt) if not yt % 20 else '' for yt in yticks]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        ax.grid(axis='both')

        ax2 = ax.twinx()
        ax2.set_ylim(0, pop / 1000000)
        ax2.set_yticks(list(range(0, 20, 2)))
        ax2.set_ylabel('millones de personas')

        ax.legend(loc='upper left')
        
        fig.tight_layout()
        if show:
            fig.show()
        fig.savefig('output/contrib/fraccion_vacunados_fecha.pdf')

# (dosis, fecha, edad), vacunados = total_vacunados()
# avance_fecha(plot=True)
# avance_edad(plot=True)
vacunas_adquiridas(plot=True)

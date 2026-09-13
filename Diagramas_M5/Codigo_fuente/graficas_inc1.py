# -*- coding: utf-8 -*-
"""Figuras 7.1 a 7.3 del Incremento 1, generadas desde el Excel de esfuerzo acumulado."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

OUT = '/home/claude/final/img'
os.makedirs(OUT, exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'
MORADO, MORADO_CLARO, GRIS = '#7030A0', '#C9A6E0', '#808080'

datos = json.load(open('/home/claude/final/sprint1.json'))
tareas, serie = datos['tareas'], datos['serie']

TOT_EST = sum(t['est'] for t in tareas)
TOT_REAL = sum(t['real'] for t in tareas)
print('Sprint 1: %d tareas · %d HH est / %d HH real · desviación %d HH (%.1f %%)'
      % (len(tareas), TOT_EST, TOT_REAL, TOT_REAL - TOT_EST,
         100.0 * (TOT_REAL - TOT_EST) / TOT_EST))


def base(titulo, xlabel, ylabel, figsize=(9.0, 4.2)):
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    ax.set_title(titulo, fontsize=11, fontweight='bold', color='#333333', pad=10)
    ax.set_xlabel(xlabel, fontsize=8.5)
    ax.set_ylabel(ylabel, fontsize=8.5)
    ax.grid(True, linewidth=0.4, color='#DDDDDD')
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=7)
    return fig, ax


# ------------------------------------------------- 7.1 esfuerzo por grupo
grupos = []
for t in tareas:
    g = t['grupo'].split('—')[-1].strip()
    if not grupos or grupos[-1][0] != g:
        grupos.append([g, 0, 0])
    grupos[-1][1] += t['est']
    grupos[-1][2] += t['real']

etq = [g[0].replace(' y ', '\ny ') for g in grupos]
est = [g[1] for g in grupos]
real = [g[2] for g in grupos]
x = list(range(len(grupos)))
fig, ax = base('Esfuerzo estimado y real por grupo de tareas — Incremento 1',
               'Grupo de tareas', 'Horas-hombre [HH]', figsize=(9.0, 4.4))
b1 = ax.bar([i - 0.2 for i in x], est, width=0.4, color=MORADO_CLARO,
            edgecolor=MORADO, linewidth=0.8, label='Estimado')
b2 = ax.bar([i + 0.2 for i in x], real, width=0.4, color=MORADO,
            edgecolor=MORADO, linewidth=0.8, label='Real')
for barras in (b1, b2):
    for b in barras:
        ax.annotate('%d' % b.get_height(), (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha='center', va='bottom', fontsize=7, color='#444444')
ax.set_xticks(x)
ax.set_xticklabels(etq, fontsize=7.5)
ax.set_ylim(0, max(real + est) * 1.18)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(OUT + '/Fig_7.1_Esfuerzo_por_grupo.png', bbox_inches='tight')
plt.close(fig)

# ------------------------------------------------- serie del sprint 1
etqs = [s['fecha'] for s in serie]
xs = list(range(len(serie)))
N = len(serie) - 1
# la curva planificada quema linealmente el esfuerzo ESTIMADO; la real, el efectivamente consumido
acum_plan = [round(TOT_EST * n / N) for n in xs]
pend_plan = [TOT_EST - v for v in acum_plan]
acum_real = [s['acum_real'] for s in serie]
pend_real = [TOT_REAL - v for v in acum_real]
print('burn-down real: %d -> %d · plan: %d -> %d' % (pend_real[0], pend_real[-1],
                                                     pend_plan[0], pend_plan[-1]))
print('burn-up real: %d -> %d · plan: %d -> %d' % (acum_real[0], acum_real[-1],
                                                   acum_plan[0], acum_plan[-1]))
json.dump(dict(etqs=etqs, acum_plan=acum_plan, pend_plan=pend_plan,
               acum_real=acum_real, pend_real=pend_real),
          open('/home/claude/final/serie_inc1.json', 'w'), ensure_ascii=False)


def curva(nombre, titulo, ylabel, plan, real_, etiqueta):
    fig, ax = base(titulo, 'Día de sprint (Sprint 1)', ylabel)
    ax.plot(xs, plan, color=GRIS, ls='--', lw=1.8, label='Planificado')
    ax.plot(xs, real_, color=MORADO, lw=2.4, label=etiqueta)
    ax.set_xticks(xs)
    ax.set_xticklabels(etqs, rotation=45, ha='right', fontsize=7)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT + '/' + nombre, bbox_inches='tight')
    plt.close(fig)


curva('Fig_7.2_Burndown_inc1.png', 'Burn-Down del Incremento 1 — esfuerzo pendiente',
      'HH pendientes del incremento', pend_plan, pend_real, 'Pendiente real · Incremento 1')
curva('Fig_7.3_Burnup_inc1.png', 'Burn-Up del Incremento 1 — esfuerzo acumulado',
      'HH acumuladas del incremento', acum_plan, acum_real, 'Acumulado real · Incremento 1')

print('figuras generadas en', OUT)

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams["figure.figsize"] = (6, 6)
##set font size
font={'family': 'sans-serif',
      'weight': 'normal',
      'size':14}
plt.rc('font', **font)
import pandas as pd


def eng_stress_eng_strain(x=None, y=None, **path_dic):
    """ PLOT THE FORCE VERSUS DISPLACEMENT
    COMPARE EXPERIMENTAL DATA TO SIMULATED DATA.
    WE NEED TO SHOW PERFECT MATCH UP TO UTS"""
    fig, ax2d = plt.subplots()
    ax = np.ravel(ax2d)

    ax[0].plot(x, y, color='k', marker='o', label='Experimental')

    # AXES LIMITS
    ax[0].set_xlim([0, (1.1 * max(x))])
    ax[0].set_ylim([0, (1.1 * max(y))])

    # AT LEAST FIVE TICK MARKS ON X AND Y AXES
    ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
    ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))
    # AXES LABELS
    ax[0].set_xlabel('Engineering strain, mm/mm')
    ax[0].set_ylabel('Engineering stress, MPa')

    ax[0].legend(bbox_to_anchor=(1, 0),
                 loc='lower right',
                 borderaxespad=0,
                 frameon=False)
    # save figure
    plt.savefig(os.path.join(path_dic['curr_results'], 'ENG_SS.png'),
                dpi=300,
                bbox_inches='tight')
    # plt.show()
    plt.close('all')

def plot_sec_der_peaks(true_strain=None, true_stress=None,
                       interp_strain=None, interp_stress=None,
                       img_name='unnamed_image', data_dic=None,
                       **path_dic):
    # PLOT TO SHOW THE CURVE AND SECOND DERIV
    fig, ax2d = plt.subplots()
    ax = np.ravel(ax2d)
    ax2 = ax[0].twinx()
    # PLOT DATA
    p1 = ax[0].plot(true_strain,
                    true_stress,
                    marker='o',
                    color='k',
                    linestyle='None',
                    label='experimental data')
    p2 = ax[0].plot(interp_strain,
                    interp_stress,
                    color='k',
                    linestyle='--',
                    label='interpolated data')
    p3 = ax2.plot(interp_strain,
                  data_dic['SEC_DER'],
                  color='r',
                  label='second derivative of strain')
    # PLOT PEAKS
    p4 = ax2.plot(interp_strain[data_dic['ZERO']],
                  data_dic['SEC_DER'][data_dic['ZERO']],
                  'gx',
                  label='end of linear region')
    p5 = ax[0].plot(interp_strain[data_dic['ZERO']],
                    interp_stress[data_dic['ZERO']],
                    'go',
                    label='identified yield strength')
    p6 = ax[0].plot(interp_strain,
                    data_dic['E']*interp_strain,
                    label='Regression line')

    # ##ADD TEXT SHOWING YIELD STRENGTH VALUE & WINDOW LENGTH
    ax[0].text(x=0.02, y=0.95,
               s='Yield strength: %s MPa\nWindow Length: %s\nR$^2$ score: %s'
                 %(str(round(interp_stress[data_dic['ZERO']], 2)),
                   str(data_dic['WINDOW_LENGTH']),
                   str(round(data_dic['r2'], 3))),
               horizontalalignment='left',
               verticalalignment='center',
               transform=ax[0].transAxes)

    # AXES LIMITS
    ax[0].set_xlim([0, max(true_strain) + (max(true_strain) * 0.1)])
    ax[0].set_ylim([0, max(interp_stress) + (max(interp_stress) * (0.1))])

    # AT LEAST FIVE TICK MARKS ON X AND Y AXES
    ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
    ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))
    ax2.yaxis.set_major_locator(plt.MaxNLocator(6))

    # FORMAT XLABELS TO BE % RATHER THAN mm/mm
    locs, labels = plt.xticks()
    labels = [round(float(item) * 100, 2) for item in locs]
    plt.xticks(locs, labels)

    # AXES LABELS
    ax[0].set_xlabel('True strain, %')
    ax[0].set_ylabel('True stress, MPa')
    ax2.set_ylabel('Second order derivative')

    mylines = p1 + p2 + p3 + p4 + p5 + p6
    labs=[l.get_label() for l in mylines]
    ax[0].legend(mylines, labs,
                 bbox_to_anchor=(1.2, 1),
                 loc='upper left',
                 borderaxespad=0,
                 frameon=False)
    # ##save figure
    plt.savefig(os.path.join(path_dic['curr_results'], img_name + '.png'),
                dpi=300,
                bbox_inches='tight')
    plt.close('all')

def plot_all_slopes(true_strain=None,
                    true_stress=None,
                    m_range=None,
                    uts_dic=None,
                    path_dic=None):
    fvd = pd.read_csv(path_dic['exp_fvd'], header=[0, 1]).droplevel(level=1, axis=1)
    # ##PLOT ENG STRESS-STRAIN AND TRUE STRESS-STRAIN (ORIG)
    fig, ax2d = plt.subplots()
    ax = np.ravel(ax2d)

    ## PLOT TRUE DATA
    ax[0].plot(true_strain, true_stress, color='k', linestyle='--', label='True')
    # ##EXTEND TRUE STRESS - TRUE STRAIN USING SLOPES
    for j, m in enumerate(m_range):
        # ##THE INTERCEPT IS A FUNCTION OF SIGMA TRUE UTS AND
        # ##EPSILON TRUE UTS (C = SIG_T - M*ESP_T)
        c = uts_dic['TRUE_STRESS'] - (m * uts_dic['TRUE_STRAIN'])
        # ##CALCULATE TRUE STRESS/STRAIN DATA BASED ON LINEAR RELATIONSHIP
        extend = len(fvd) - len(true_strain)
        # ##EXTEND STRAINS
        estrain = np.linspace(true_strain.iloc[-1] + 1e-4, 2, num=extend).reshape(-1, 1)
        estress = m * estrain + c
        # ##PLOT THE NEW SLOPE TO FIGURE
        ax[0].plot(estrain, estress, label='Slope: %s' % (round(m, 2)))
    # ##LIMIT AXES
    # FORMAT XLABELS TO BE % RATHER THAN mm/mm
    locs, labels = plt.xticks()
    labels = [round(float(item) * 100, 2) for item in locs]
    plt.xticks(locs, labels)

    # ##AXES LIMITS
    ax[0].set_xlim([0, 2])
    ax[0].set_ylim([0, 1000])
    # AXES LABELS
    ax[0].set_xlabel('True strain, %')
    ax[0].set_ylabel('True stress, MPa')
    # ##PLOT VALUES
    ax[0].legend(bbox_to_anchor=(1.1, 1),
                 loc='upper left',
                 borderaxespad=0,
                 frameon=False)
    # ##save figure
    plt.savefig(os.path.join(path_dic['curr_results'], 'COMPARE_SLOPES.png'),
                dpi=300,
                bbox_inches='tight')
    plt.close('all')

def compare_sim_smooth(df1=None,
                       df2=None,
                       job_name=None,
                       paths=None):

    """
    Function to plot explicit smoothed data against original explicit data

    :param df1: Original explicit data
    :param df2: Smoothed explicit data
    :param job_name: Job name
    :param paths: dictionary of paths for file saving
    :return:
    """

    # ##FIGURE OPTIONS
    fig, ax2d = plt.subplots()
    ax = np.ravel(ax2d)

    ax[0].plot(df1['U'], df1['RF'], label='Original')
    ax[0].plot(df2['U'], df2['RF'], label='Smoothed')

    # ##AXES LIMITS
    ax[0].set_xlim([0, 3])
    ax[0].set_ylim([0, max(df1['RF'].max() * 1.1, df2['RF'].max() * 1.1)])
    # AXES LABELS
    ax[0].set_xlabel('Displacement, mm')
    ax[0].set_ylabel('Force, kN')
    # ##PLOT VALUES
    ax[0].legend(bbox_to_anchor=(0.1, 0.1),
                 loc='lower left',
                 borderaxespad=0,
                 frameon=False)
    # ##save figure
    plt.savefig(os.path.join(paths['curr_results'],
                              job_name  + '_SMOOTHING.png'),
                dpi=300,
                bbox_inches='tight')
    plt.close('all')
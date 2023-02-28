# A Machine Learning Approach to Automate Ductile Damage Parameter Selection in Finite Element Simulations

The aim of this project was to use Bayesian Optimisation (BO) to automate the selection of ductile damage parameter values based on the resulting fit between experimental test data and simulated Finite Element (FE) data.
The FE solver used for this project is Abaqus 2021.
The predominate coding language is Python V3.9 though some code, specifically FE model building and postprocessing, are written in Python V2.7.

**Paper abstract:**
A key limitation of finite element analysis is accurate modelling of material damage.
While additional material models exist that improve correlations between simulated damage and experimental data, these models often require additional parameters that are difficult to estimate.
Here Bayesian optimisation, a machine learning technique, is shown to successfully identify material model parameters.
The Bayesian derived material model parameters result in simulated output with less than 2% error compared to experimental data.
The framework detailed here is fully autonomous, requiring only basic information that can be derived from a simple tensile test.
This framework has been successfully deployed to three datasets of P91 material tested at ambient (20 degrees Celsius) and higher (500 degree Celsius) temperatures.
Hyperparameters are shown to affect individual parameter values due to the ill-posedness of the problem.

This repository has two main directories:
1. Bayesian optimisation: This directory holds source code and results data.
	* A_RAW_DATA: Directory with design of experiments (DOE) arrays
		* L12.csv: DOE for 12 experiments based on eight variables at two levels
	* B_SCR: Directory of source code that is called when main.py is executed
		* aba_build_expl.py: Python V2.7 code to build Abaqus explicit model
		* aba_pp_expl.py: Python V2.7 code to extract data from Abaqus simulation
		* abaqus_function.py: Python V3.9 functions to build abaqus command prompt submitting an Abaqus simulation via subprocess
		* Acquisition_utilities.py: Python V3.9 Create Acquisition function object
		* clean_fea_dir.py: Python V3.9 function to remove unwanted abaqus generated files from results (*.sim, *.log etc)
		* Continious_Bayesian_Optimisation.py: Python V3.9 Create Bayesian optimisation object
		* csv_functions.py: Python V3.9 functions to initialise and write data to csv files
		* DoE.py: Python V3.9 function to read data from A_RAW_DIR and map parameter bounds to DoE style array
		* error_function.py: Python V3.9 function to read, manipulate and modify experimental and simulation data to calculate loss function value (MAPE)
		* general_functions.py: Python V3.9 various functions for converting data formats such as merging dictionaries and reading/writing dictionaries to string via JSON
		* material_properties.py: Python V3.9 function to extrapolate beyond ultimate tensile strength for a slope value that has not been previously assessed
		* pandas_functions.py: Python V3.9 function to compare multiple dataframes and get unique rows only (stops abaqus repeating multiple analyses for identical ductile damage parameter combinations)
		* Parameter_Space.py: Python V3.9 Creates parameter space object
		* plots.py: Python V3.9 creates various plots used to assess results
		* results_plots.py: Python V3.9 creates key results for each dataset comparing top results to experimental data
		* termination_function.py: Python V3.9 function to assess whether BO code should exit early
		* virtual_experiment.py: function that assesses whether next ductile damage parameter combination is choosen from existing DOE array or from BO generated values (acquisition function)

	* RESULTS: Directory of results extracted from simulations
      * Files:
        * .gitignore: File extensions not tracked on git due to space issues (*.odb)
		  main.py: Main scripting file accesses code in B_SCR and generates results in RESULTS directory.
      * Subdirectories:
          * Dataset 1 (H1): L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=500, random samples=50,000
          * Dataset 2: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_1, optimisation samples=500, random samples=50,000
          * Dataset 3: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_500, optimisation samples=500, random samples=50,000
          * H2: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=100, random samples=50,000
          * H3: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=500, random samples=10,000
          * H4: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=100, random samples=10,000
        * Each subdirectory contains data files as follows:
          * OUTPUT.csv: Master file tracking bayesian optimisation:
            * iteration number (JOB_NUM): An integer value used for counting the number of simulations.
            * Ductile damage parameter values (Q1, Q2, Q3, EN, SN, FN, F, M), floating point values.
            * Loss function calculation (ORIG_MAPE) a floating point value representing the percentage similarity between experimental data and simulated output.
            * Weight assigned to acquisition function (KAPPA also denoted as $\sqrt{B_t}$) in the case of this work a fixed value of 2.5 was used.
            * Simulation time (SIM_TIME) a floating point value representing the time in seconds to submit the abaqus job request, execute aba_build_exp.py, run the simulation, extract data from simulation via executing aba_pp_expl.py.
          * The OUTPUT.csv file is generated, in part, from data collected in specific files. Here '*' refers to the bayesian iteration number which can be cross-referenced in OUTPUTS.csv. Specific files contributing to OUTPUTS.csv are as follows:
            * JOB*.inp: Abaqus input file generated by executing aba_build_expl.py.
            * ABA_JOB*.csv: File contains array of true stress-plastic strain values. These data also appear in Abaqus input file (JOB*.inp) under the *PLASTIC keyword. True stress in MPa, plastic strain in mm/mm. 
            * EXP_EXTRAP.csv: Array of interpolated values for displacement (U) and applied load (RF) relating to the experimental data. Units of mm, kN respectively. 
            * JOB*_ENERGY.csv: Array of floating point values for TIME, ALLKE, ALLIE. Where time is the abaqus time incrementation (0 to 1), ALLKE represents the kinetic energy of the simulation, ALLIE represents the internal energy of simulation. Energy values in millijoules.
            * JOB*_JSON.txt: Text version of python dictionary, where dictionary contains ductile damage model parameters, paths to the location of files required for aba_build_expl.py to build and execute simulation.
            * JOB*_LD_DATA.csv: Array of floating point values for applied load (RF) and displacement (U) extracted from abaqus simulation through execution of aba_pp_expl.py. Units in Newtons and mm, respectively. 
            * JOB*_SIM_EXTRAP.csv: Interpolated version of JOB*_LD_DATA.csv where minimum displacement increment is modified to $\Delta u_{min}$ (see preprint for additional information). Units in mm (U) and kN (RF). 
            * JOB*_SIM_EXTRAP_NOSMOOTH.csv: Identical to JOB*_SIM_EXTRAP.csv
            * JOB*_SIM_EXTRAP_SMOOTH.csv: Filtered version of JOB*_SIM_EXTRAP.csv to smooth dynamic effects. Units in mm (U) and kN (RF).

2. Preprint: This directory holds latex code, figures, tables and auxiliary information pertaining to the preprint.
   * Files:
      * .gitignore: File extensions not tracked on git due to space issues (*.pdf)
   * Subdirectories:
       * AUXIL: Latex auxiliary files
         * document.aux
         * document.bbl
         * document.blg
         * document.loc
         * document.log
         * document.soc
         * document.spl
       * DOCUMENT: Directory in which main latex files (*.tex, *.bib) are stored
         * document.tex: main latex document
         * BO_PAPER.bib: bibliography for main latex document
       * FIGURES: Directory of figures generated as part of this research used in the preprint
         * ABAQUS_SLOPE_COMPARISON.png
           * Image showing extrapolation of true stress-true strain beyond ultimate tensile strength.
         * BO_FLOWCHART.png
           * Flowchart of bayesian optimisation process
         * DIAGRAM_ENG_SS.png
           * Engineering stress-strain and key values
         * DOE_FLOWCHART.png
           * Flowchart of design of experiments process
         * EXPERIMENTAL_RESULTS.png
           * Force-displacement chart showing three experimental test results
         * FIGURES_INFO.txt
           * Text file linking figures to placement in document.tex
         * FLOWCHART_LEGEND.png
           * Legend for flowcharts
         * HYPERPARAMETERS.png
           * Load-displacement results for simulations with varying hyperparameters
         * MODEL_2D_3D.png
           * Diagram of specimen orientation and boundary conditions in idealised 2D simulation
         * P91_20_1_FASTEST_ITERATION.png
           * Comparison of bayesian optimisation ductile damage simulation for the fastest iteration (lowest JOB_NUM) to reach target mean average percentage error (MAPE <= 2%) with experimental data (Dataset 2)
         * P91_20_2_FASTEST_ITERATION.png
           * Comparison of bayesian optimisation ductile damage simulation for the fastest iteration (lowest JOB_NUM) to reach target mean average percentage error (MAPE <= 2%) with experimental data (Dataset 1)
         * P91_500_FASTEST_ITERATION.png
           * Comparison of bayesian optimisation ductile damage simulation for the fastest iteration (lowest JOB_NUM) to reach target mean average percentage error (MAPE <= 2%) with experimental data (Dataset 3)
         * SECOND_DERIV.png
           * Diagram detailing the automated method defining yield stress and Young's modulus for three experimental tests.
       * OUT: Directory in which PDF of *.tex is stored
       * TABLES: Directory of tables used in preprint. Generated as standalone *.tex files that are called in to *.tex document
         * BO_PARAMETER_VALUES.tex
           * Table comparing ductile damage model parameter values estimated using bayesian optimisation framework for three datasets.
         * HYPER_PARAMETER_VALUES.tex
           * Table comparing ductile damage model parameter values for dataset 1 with modifications to acquisition function hyperparameter values. 
         * L12.tex
           * Table showing design of experiments for eight parameters with two levels
         * PARAMETER_SPACE_ALL.tex
           * Table showing the minimum and maximum boundaries for each ductile damage parameter.
	  











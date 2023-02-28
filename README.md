# A Machine Learning Approach to Automate Ductile Damage Parameter Selection in Finite Element Simulations

The aim of this project was to use Bayesian Optimisation (BO) to automate the selection of ductile damage parameter values based on the resulting fit between experimental test data and simulated Finite Element (FE) data.
The FE solver used for this project is Abaqus 2021.
The predominate coding language is Python V3.9 though some code, specifically FE model building and postprocessing, are written in Python V2.7. 

**Paper abstract**
A key limitation of finite element analysis is accurate modelling of material damage.
While additional material models exist that improve correlations between simulated damage and experimental data, these models often require additional parameters that are difficult to estimate.
Here Bayesian optimisation, a machine learning technique, is shown to successfully identify material model parameters.
The Bayesian derived material model parameters result in simulated output with less than 2~\% error compared to experimental data.
The framework detailed here is fully autonomous, requiring only basic information that can be derived from a simple tensile test.
This framework has been successfully deployed to three datasets of P91 material tested at ambient ($20~\degree$C) and higher ($500~\degree$C) temperatures.
Hyperparameters are shown to affect individual parameter values due to the ill-posedness of the problem.

This repository has two main directories: 
1. Bayesian optimisation: This directory holds source code and results data. 
   * A_RAW_DATA: Directory with design of experiments (DOE) arrays
   * B_SCR: Directory of source code that is called when main.py is executed
   * RESULTS: Directory of results extracted from simulations
     * Dataset 1 (H1): L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=500, random samples=50,000
     * Dataset 2: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_1, optimisation samples=500, random samples=50,000 
     * Dataset 3: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_500, optimisation samples=500, random samples=50,000
     * H2: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=100, random samples=50,000
     * H3: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=500, random samples=10,000
     * H4: L12 DOE array, no restrictions on termination function, kappa=2.5, material test P91_20_2, optimisation samples=100, random samples=10,000
   .gitignore: File extensions not tracked on git due to space issues (*.odb)
   main.py: Main scripting file accesses code in B_SCR and generates results in RESULTS directory.

2. Preprint: This directory holds latex code, figures, tables and auxiliary information pertaining to the preprint.
   * AUXIL: Latex auxiliary files 
   * DOCUMENT: Directory in which main latex files (*.tex, *.bib) are stored
   * FIGURES: Directory of figures generated as part of this research used in the preprint
   * OUT: Directory in which PDF of *.tex is stored
   * TABLES: Directory of tables used in preprint. Generated as standalone *.tex files that are called in to *.tex document
   .gitignore: File extensions not tracked on git due to space issues (*.pdf)











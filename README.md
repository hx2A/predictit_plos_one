# Understanding Market Functionality and Trading Success

## Authors

* David Rothchild ([David@ResearchDMR.com](David@ResearchDMR.com))
* James Schmitz ([james.schmitz@nyu.edu](james.schmitz@nyu.edu))

## Abstract

> We examine individual-level trading data from several markets in the PredictIt exchange to determine what strategies correlate with financial success. PredictIt provides many markets with futures contracts linked to political issues, ranging from ongoing policy outcomes to political elections. High fees along with restrictions blocking automatic trading and constraining a one-to-one match between people and accounts, combine to severely limit the upside to investment returns over the fixed costs: this ensures that traders are all retail investors. We have the individual-level data from two markets: Democratic and Republican Iowa Caucuses in 2016. This data includes all orders and trades from every trader across the markets. We are able to fully reconstruct market activity and study trader behavior both within and between markets. We show that understanding how markets and trades works is more important to financial success than proxies for (1) confidence or funding (2) information or objectivity in trading. The work should be a call-to-action in favor of simplifying markets and trading for any exchange with retail investors, and for more research into effects of differential trading efficiency in all financial markets.

# License

![Creative Commons License][license] The code supporting this research paper is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License][license_link].

[license]: https://i.creativecommons.org/l/by-sa/4.0/80x15.png
[license_link]: http://creativecommons.org/licenses/by-sa/4.0/

# Data

The data for this research paper was provided us by [PredictIt](http://predictit.org).

## Data Availability

The authors confirm that, for approved reasons, some access restrictions apply to the data underlying the findings. The trading data analyzed in the work was not directly collected by the authors, but provided by an online trading company, according to their data privacy policy and their agreement with PredictIt. Hence, due to both ethical and legal concerns, the authors cannot make the data public available without the permission of the company. However, upon request, they can refer any researchers to that company, which provides access to past data (and specifically – the same data that was used for this research) through their platform to academic researchers who sign an agreement with them (which is what the authors did). Hence it is totally possible for other researchers to reach the data owner by contacting [David@ResearchDMR.com](David@ResearchDMR.com).

# Setup

Install [Anaconda](https://www.anaconda.com/distribution/#download-section) on your computer and create a Conda environment:

```
conda env create -f environment.yml
```

Activate the new Conda environment:

```
conda activate predictit_plos_one
```

Install custom research tools:

```
python setup.py build
pip install -e .
```

Obtain PredictIt data files and place in the `data` directory. Then run the analysis and create the data files. This will take several hours but only has to be done once.

```
python scripts/iowa_dem_caucuses.py
python scripts/iowa_gop_caucuses.py
```

Launch Jupyter Notebook:

```
jupyter notebook
```

# Citation

```
@article{rothschild_schmitz_2019,
  author={Rothschild, D and Schmitz, J},
  title={Understanding Market Functionality and Trading Success.},
  journal={PLoS ONE},
  volume={14},
  number={8},
  year={2019},
  DOI={10.1371/journal.pone.0219606}
}
```

# Acknowledgements

We thank David Pennock, Rupert Freeman, and Andreas Katsouris for reading early drafts of the paper. Rajiv Sethi and Koleman Strumpf for their useful conversation. Also, PredictIt and John Phillips for working with us on both data acquisition and unique issues with the data cleaning.

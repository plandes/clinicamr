# Clincial Domain Abstract Meaning Representation Graphs

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.9][python39-badge]][python39-link]

This package parses clinical notes in to Abstract Meaning Representation Graphs
(AMR).  It uses the following packages to create the graphs and features:

* THYME [AMR SPRING parser] to create the graphs
* [MedCAT] for entity linking `CUI` attribution nodes
* [MedSecId] for the clinical note sectioning
* [Zensols Natural Language Parsing] for language parsing and feature creation


## Documentation

See the [full documentation](https://plandes.github.io/clinicamr/index.html).
The [API reference](https://plandes.github.io/clinicamr/api.html) is also
available.


## Obtaining

The library can be installed with pip from the [pypi] repository:
```bash
pip3 install zensols.clinicamr
```


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## Citation

This package and the [amrspring Docker image] uses the original [AMR SPRING
parser] source code base from the paper *"One SPRING to Rule Them Both:
Symmetric AMR Semantic Parsing and Generation without a Complex Pipeline"*:

```bibtex
@inproceedings{bevilacquaOneSPRINGRule2021,
  title = {One {{SPRING}} to {{Rule Them Both}}: {{Symmetric AMR Semantic Parsing}} and {{Generation}} without a {{Complex Pipeline}}},
  shorttitle = {One {{SPRING}} to {{Rule Them Both}}},
  booktitle = {Proceedings of the {{AAAI Conference}} on {{Artificial Intelligence}}},
  author = {Bevilacqua, Michele and Blloshmi, Rexhina and Navigli, Roberto},
  date = {2021-05-18},
  volume = {35},
  number = {14},
  pages = {12564--12573},
  location = {Virtual},
  url = {https://ojs.aaai.org/index.php/AAAI/article/view/17489},
  urldate = {2022-07-28}
}
```


## License

[MIT License](LICENSE.md)

Copyright (c) 2024 - 2025 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.clinicamr/
[pypi-link]: https://pypi.python.org/pypi/zensols.clinicamr
[pypi-badge]: https://img.shields.io/pypi/v/zensols.clinicamr.svg
[python39-badge]: https://img.shields.io/badge/python-3.9-blue.svg
[python39-link]: https://www.python.org/downloads/release/python-390

[AMR SPRING parser]: https://github.com/SapienzaNLP/spring
[MedCAT]: https://github.com/CogStack/MedCAT
[MedSecId]: https://github.com/plandes/mimicsid
[Zensols Natural Language Parsing]: https://github.com/plandes/nlparse

[amrspring Docker image]: https://github.com/plandes/amrspring?tab=readme-ov-file#docker

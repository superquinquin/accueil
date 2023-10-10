# Accueil
**A minimalistic application for managing foodCoop shifts and shifts registrations**

* [Guideslines](#Contributions-Guideslines)
  * [How to contribute](#How-to-contribute)
  * [On what to contribute](#On-what-to-contribute)

## Contributions Guideslines
A few features remains to be implemented.

Then all the efforts we be focused on realeasing a v1.0, changes are expected to be similar to those done in the [Scannettes App](https://github.com/superquinquin/inventory-bl-scanner-webapp/tree/main) such as:
* build update, moving to poetry.
* renewing config handling and parsing.
* adding config validation
* refactor backend, which is currently a large partchwork of features made on the go to meet BDM expectations.

### How to contribute
* Create a branch based on main. name your branch after the feature/fix you want to implement. prefix the branch witht the kind of change you will add ( feature/xxx ; fix/xxx ; refactor/xxx.. )
* For any contribution over the python parts, make sure to use formatter such as [BLack Formatter](https://github.com/psf/black) and [Flake8](https://github.com/PyCQA/flake8)
  * Some pre-commit hooks will be added when I have the time to switch from pipenv to Poetry build.
*  Similarly for JS however, I don't know any tools nor did proper formatting myself yet.
*  Format your commits using tools such as [Commitizen](https://github.com/commitizen/cz-cli) or any equivalent tools.
*  PR must heads towards the main branch

### On what to contribute
Maybe those points will pop as Github issues if I have the time.

**Backend**

Features to add before moving focus:
* [ ] Find key&value determining if a Coop is a shift leader or not.
  * add to Member model
  * add visual clue in the interface.
* [ ] Filter associate members, on whether they are eaters or not. Filter out eaters as they cannot present themself for a shift.
* [ ] Restructure emails ( destructured by lack of time, most of them just repeat themselves ). modify email implementation accordingly. 


**Frontend**

Has to be determined, I don't see much things to changes/add

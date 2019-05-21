# Locales

## Creating a new locale
Use [this](https://en.wikipedia.org/wiki/ISO_3166-1#Officially_assigned_code_elements) list to find your ISO 3166-1 Alpha-2 code.  
The code has to be lower case (You have to convert it).
  
Then create a file named YOUR_LOCALE.json in this directory with this content: "{}" (without the Double Quotation Marks).  
  
Then start using the tool as described below.

## Translating strings missing in your locale
We wrote a little tool for this task:  
```bash
node translation-helper.js
```
You will be asked to select a language to translate.  
Running the tool looks like this:
```
Languages you can translate: ar, da, de, es, fr, hr, it, ja, nl, pl, pt-br, ru, sv, zh-cn, zh-hk, zh-tw
Which language do you want to translate: de

country-panel.electricity [Electricity]: Elektrizität
zoneShortName.IQ-KUR.countryName [Iraq]: Irak
...
```

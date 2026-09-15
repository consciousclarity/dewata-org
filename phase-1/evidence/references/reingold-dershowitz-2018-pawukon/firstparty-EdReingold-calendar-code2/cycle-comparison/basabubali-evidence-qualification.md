# BASAbali evidence qualification

**Date:** 2026-09-15

## What basabubali.org is
- Community-curated Balinese dictionary and language wiki
- URL: https://basaibubali.org/{Wewaran}
- Maintained by BASAbali Wiki project
- Includes word definitions, root etymologies, usage examples
- NOT a traditional Lontar or scholarly Wariga text

## What basabubali.org provides for our analysis
- Pancawara, Caturwara, Sangawara, Dasawara, Dwiwara, Ekawara formulas
- Each formula is given as: `rule: <formula>; remainder determines day name: <mapping>`
- No Astawara page content (page exists but is empty)
- No before/after-Dungulan offsets
- No exception rules
- No joint Caturwara/Astawara treatment
- The formulas presented are simple modular arithmetic

## Specific formulas extracted (with full page context)

### Pancawara (basaibubali.org/Pancawara)
```
week en five day week en
rule: (bilangan uku x 7 + bilangan Saptawara)/5 en
remainder determines day name: 1 = Umanis, 2 = Pahing, 3 = Pon, 4 = Wage, 5 = Kliwon en
```

### Caturwara (basaibubali.org/Caturwara)
```
week en four day week en
rule for determining which of the four days: (bilangan uku x 7 + bilangan saptawara)/4 en
remainder determines day name: 1 = Sri, 2 = Laba, 3 = Jaya, 0 = Menala en
```

### Sangawara (basaibubali.org/Sangawara)
```
week en nine day week en
rule: (bilangan uku x 7 + bilangan Saptawara)/9 en
remainder determines day name: 1 = Dangu, 2 = Jangur, 3 = Gigis, 4 = Nohan, 5 = Ogan, 6 = Erangan, 7 = Urungan, 8 = Tulus, 0 = Dadi en
```

### Dasawara (basaibubali.org/Dasawara)
```
week en ten day week en
rule for determining day name: urip Pancawara + urip Saptawara + 1)/10 en
remainder determines day name: 1 = Pandita, 2 = Pati, 3 = Suka, 4 = Duka, 5 = Sri, 6 = Manuh, 7 = Manusa, 8 = Eraja, 9 = Dewa, 0 = Raksasa en
```

### Dwiwara (basaibubali.org/Dwiwara)
```
week en two day week: rule: urip Pancawara + urip Saptawara en
if sum is odd then the day is Pepet en
if the sum is even the day is Menga en
```

### Ekawara (basaibubali.org/Ekawara)
```
week en one-day week: Luan or empty (i.e. there is no ekawara day that particular day) en
rule to determine day name: Urip Pancawara + Urip Saptawara en
if sum is odd, Ekawara is Luan en
if sum is even, Ekawara is empty (Tunggal, Padat) en
```

### Astawara (basaibubali.org/Astawara)
"There is currently no text in this page. You can search for this page title in other pages..."

## What basabubali.org does NOT provide
- No description of the special-case structure for Caturwara/Astawara (penultimate-day-twice-around-day-72)
- No description of the Sangawara first-day-3x-in-first-week rule
- No mention of pangunalatri or ngunaratri cycles
- No exception rules
- No before/after-Dungulan offsets
- No joint Caturwara/Astawara treatment

## Per user instruction: "A formula excerpt without its surrounding convention is insufficient to establish a competing semantic ruleset."

The BASAbali formulas are presented as standalone modular arithmetic rules. They do NOT describe:
1. The conditions under which the formula applies (e.g., on which specific cycle days special handling might override)
2. How the formula relates to other wewaran in the cycle
3. The cultural context of why this formula is used
4. Whether there are exceptions for specific wuku/days

Therefore BASAbali's simple-modular formulas cannot be claimed as "the canonical ruleset" or as "competing with CALENDRICA". They are community-curated representations that may or may not capture all the nuances of traditional Wariga practice.

## Comparison with CALENDRICA / Dewata special-case handling

| wewaran | CALENDRICA / Dewata | BASAbali | difference |
|---|---|---|---|
| Caturwara | special case around day 72 (CAL: amod(bali-asatawara, 4); DEW: hardcoded day-72/73) | (uku*7+saptawara)/4 simple modular | CAL/DEW disagree with BASAbali on positions where special case differs from simple mod |
| Sangawara | special case (CAL: max(0,day-3); DEW: days 1-3 all Dangu) | (uku*7+Saptawara)/9 simple modular | CAL/DEW disagree with BASAbali on early-cycle positions |
| Dasawara | uses urip_5 + urip_7 tables | uses urip Pancawara + urip Saptawara (different urip values!) | the urip tables are different, so the day names disagree on most positions |
| Dwara / Ekawara | uses urip sum parity (DEW) or dasawara parity (CAL) | uses urip sum parity (DEW and BASAbali agree; CAL disagrees) | CAL disagrees with BASAbali/DEW on parity convention |

## Conclusion

BASAbali:
- Confirms Pancawara convention (1=Umanis) used by CALENDRICA — this is the cultural convention
- Confirms Saptawara, Triwara, Sadwara, Caturwara, Asatawara, Sangawara NAME conventions
- Uses SIMPLE modular arithmetic for Caturwara/Sangawara (without the special-case handling)
- Does NOT establish a "competing semantic ruleset" — it provides formulas that may or may not capture the full tradition

The user instruction "A formula excerpt without its surrounding convention is insufficient to establish a competing semantic ruleset" applies: BASAbali alone is insufficient evidence to claim that the special-case structure in CALENDRICA and Dewata is wrong.

Independent academic Wariga sources (Suparta Ardhana's Pokok-Pokok Wariga, Ketut Bangbang Gde Rawi, etc.) are needed to determine whether the special-case structure is canonical or a particular author's interpretation.

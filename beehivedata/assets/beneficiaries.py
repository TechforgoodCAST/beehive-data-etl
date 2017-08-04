# beneficiary categories used
ben_categories = {
    "public": {
        "label": "The general public",
        "group": "People",
        "position": 25
    },
    "crime": {
        "label": "Affected or involved with crime",
        "group": "People",
        "position": 24
    },
    "relationship": {
        "label": "With family/relationship challenges",
        "group": "People",
        "position": 23
    },
    "disabilities": {
        "label": "With disabilities",
        "group": "People",
        "position": 22
    },
    "religious": {
        "label": "With specific religious/spiritual beliefs",
        "group": "People",
        "position": 21
    },
    "disasters": {
        "label": "Affected by disasters",
        "group": "People",
        "position": 20
    },
    "education": {
        "label": "In education",
        "group": "People",
        "position": 19
    },
    "unemployed": {
        "label": "Who are unemployed",
        "group": "People",
        "position": 18
    },
    "ethnic": {
        "label": "From a specific ethnic background",
        "group": "People",
        "position": 17
    },
    "water": {
        "label": "With water/sanitation access challenges",
        "group": "People",
        "position": 16
    },
    "food": {
        "label": "With food access challenges",
        "group": "People",
        "position": 15
    },
    "housing": {
        "label": "With housing/shelter challenges",
        "group": "People",
        "position": 14
    },
    "animals": {
        "label": "Animals and wildlife",
        "group": "Other",
        "position": 13
    },
    "buildings": {
        "label": "Buildings and places",
        "group": "Other",
        "position": 12
    },
    "mental": {
        "label": "With mental diseases or disorders",
        "group": "People",
        "position": 11
    },
    "orientation": {
        "label": "With a specific sexual orientation",
        "group": "People",
        "position": 10
    },
    "environment": {
        "label": "Climate and the environment",
        "group": "Other",
        "position": 9
    },
    "physical": {
        "label": "With physical diseases or disorders",
        "group": "People",
        "position": 8
    },
    "organisation": {
        "label": "This organisation",
        "group": "Other",
        "position": 7
    },
    "organisations": {
        "label": "Other organisations",
        "group": "Other",
        "position": 6
    },
    "poverty": {
        "label": "Facing income poverty",
        "group": "People",
        "position": 5
    },
    "refugees": {
        "label": "Who are refugees and asylum seekers",
        "group": "People",
        "position": 4
    },
    "services": {
        "label": "Involved with the armed or rescue services",
        "group": "People",
        "position": 3
    },
    "care": {
        "label": "In, leaving, or providing care",
        "group": "People",
        "position": 2
    },
    "exploitation": {
        "label": "At risk of sexual exploitation, trafficking, forced labour, or servitude",
        "group": "People",
        "position": 1
    }
}

# regexes used to classify the beneficiaries of a grant
ben_regexes = {
    "crime": r'\b(crim(inal|e)|justice|judicial|offenders?|custody|anti-social behaviour|prison(ers?)?|law centre|victim|murder|rape|theft|fraud)\b',  # possible confusion with "social justice" and "restorative justice",
    "relationship": r'\b(relationship|marriage|family breakdown|mediation|counselling|conflict resolution)\b',  # relationship a bit general
    "disabilities": r'\b(disabled|disabilit(ies|y)|blind(ness)?|deaf(ness)?|(hearing|sight) loss|amputee|wheel ?\-?chair|accessib(ility|le)|handicap(ped)?|less abled|sign language|impairment|visual(ly)? ?\-?impair(ment|ed))\b',
    "religious": r'\b(christ(ian)?|muslim|jew(ish)|mosque|synagogue|church|buddhis(t|m)|sikh)\b',  # bit wide, need to exclude, eg church halls
    "disasters": r'\b(flood(s|ing)?|disasters?|rescue|survivors?|tsunami|storms?|hurricane|aftermath)\b',  # need a wider range "survivors" has DV use too, rescue used a lot for animals
    "education": r'\b(schools?|pupils?|students?|school\-?age|teach(ers?|ing)|college|a ?\-?levels?|g\.?c\.?s\.?e\.?s?|key stage (1|2|3|one|two|three)|mentoring|educational|school(child|boy|girl)(ren|s)?|classroom)\b',  # need to exclude pre-school? schools are a venue for lots of activities
    "unemployed": r'\b((un)?-?employ(ed|ment)|job-?seekers?|benefit claimants?|claim benefits|jobless|out of work)\b',
    "ethnic": r'\b(b\.?a?m\.?e\.?|black|ethnic|racial|roma)\b',  # black may be too generic?
    "water": r'\b(water|sanitation|toilets?|sewage|hygien(e|ic)|wastewater)\b',  # need to exclude water sports
    "food": r'\b(food|hunger|feed|local produce|food\-?bank|fruits?|vegetables?|cook(ery|ing)|famines?|(mal)?nutrition(ist)?|meat)\b',
    "housing": r'\b(housing|homeless(ness)?|tenants?|rough ?\-?sleep(ing|ers?)|runaways?|residents?|household|shelter)\b',  # housing is a verb, and is generic
    "animals": r'\b(animals?|pets?|dogs?|cats?|horses?|wildlife|fauna|farm-animal|livestock|marine|habitat|birds?)\b',
    "buildings": r'\b((community|new|existing) building|built environment|architecture|refurbish(ing|ment)?|repairs?|restoration|(community|village) hall|Preservation Trust|Building works)\b',  # building and heritage both a bit too wide
    "mental": r'\b(mental ?\-?(health|illness(es)?|diseases?|disorders?)|depressian|schizophrenia|bi\-?polar|psychiatry|psychiatric|eating ?-?disorders?|Self ?\-?help)\b',  # mental disease could cover dementia/learning disabilities
    "orientation": r'\b(l\.?g\.?b\.?t?\.?q?\.?|lesbian|gay|bi\-?sexual|sexuality|sexual orientation|trans\-?(sexual|gender)?|homo\-?sexual|queer|cisgender|intersex)\b',  # rainbow - but children too
    "environment": r'\b(environment(al)?|climat(e|ic)|global warming|carbon|energy efficien(t|cy)|ecosystem|nature|green spaces?|bio\-?diversity|sustainab(ility|le)|countryside|garden|pond|parks?|eco\-?audit|footpaths?|wilderness|greenhouse gas|ecolog(y|ical))\b',  # environment a bti broad: learning environment, peaceful environment, etc
    "physical": r'\b(physical health|cancer|disease|illness|Down\'?s Syndrome|get fit|fitness|sport(ing|s)?|physiotherapy|Multiple Sclerosis|stroke|diabetes|Healthy Living|health ?care|blood pressure|virus|infection)\b',  # exclude mental? often says "physical and mental health"
    "organisation": r'\b((this|our) organisation|core (costs|funding))\b',  # not sure about this one!
    "organisations": r'\b(charities|local groups|community groups|social enterprises|Council for Voluntary Service|VCS)\b',
    "poverty": r'\b(poverty|deprivation|isolation|disadvantaged)\b',  # "poor" is too generic, used as an adjective
    "refugees": r'\b(asylum ?-?seekers?|refugees?|migrants?|displaced persons?)\b',  # sanctuary?
    "services": r'\b(armed forces|army|navy|air force|marines|armed services|(ex\-)?servicem(e|a)n\'?s?|veterans?|british legion|regiment(al)?|military|sailors?|soldiers?)\b',
    "care": r'\b(care ?\-?leavers?|leaving care|looked ?\-?after ?\-?(children)?|carers?|leave care)\b',  # definition of care here?
    "exploitation": r'\b((sex)? ?\-?traffic(k?ing)?|exploitation|forced labour|sex ?\-?workers?|prostitut(es?|ion))\b',

    # the following are not in the original list
    "abuse": r'\b((domestic|sexual) (violence|abuse)|violence against women|honou?r killings?|child abuse)\b',
    "addiction": r'\b(addict(ion)?|(alcohol|drug) abuse|alcohol(ism)?|drugs?|narcotics?|abstinence)\b',
    "learning disabilities": r'\b((learning|intellectual) (difficult|disabilit|disorder)(ies|y)?)\b',

    # not really beneficiaries
    # "arts-culture": r'\b(arts?|theatre|music(al)?|museums?|galler(y|ies))\b',
    # "sport-recreation": r'\b(cricket|rugby|football|Tennis|swimming)\b',
    # "research": r'\b()\b',
}


# regexes used to classify the theme of a grant
theme_regexes = {
    "Arts": r'\b(arts?|theatre|music(al)?|museums?|galler(y|ies))\b',
    "Sport and leisure": r'\b(cricket|rugby|football|Tennis|swimming)\b',
    "Climate and the environment": r'\b(environment(al)?|climat(e|ic)|global warming|carbon|energy efficien(t|cy)|ecosystem|nature|green spaces?|bio\-?diversity|sustainab(ility|le)|countryside|garden|pond|parks?|eco\-?audit|footpaths?|wilderness|greenhouse gas|ecolog(y|ical))\b',  # environment a bti broad: learning environment, peaceful environment, etc
    "Animals and wildlife": r'\b(animals?|pets?|dogs?|cats?|horses?|wildlife|fauna|farm-animal|livestock|marine|habitat|birds?)\b',
    "Community improvement and capacity building": r'\b(infrastructure|second tier|capacity building|membership body|community)\b',
    "Building and places": r'\b((community|new|existing) building|built environment|architecture|refurbish(ing|ment)?|repairs?|restoration|(community|village) hall|Preservation Trust|Building works)\b',  # building and heritage both a bit too wide
    "Organisational development": r'\b((this|our) organisation|core (costs|funding)|charities|local groups|community groups|social enterprises|Council for Voluntary Service|VCS)\b',
    "Volunteering and civic participation": r'\b(volunteer(ing|s)?|civic|participation|unpaid|voluntary)\b',
    "Policy development": r'\b(policy development|developing policy)\b',
    "Crime and justice": r'\b(crim(inal|e)|justice|judicial|offenders?|custody|anti-social behaviour|prison(ers?)?|law centre|victim|murder|rape|theft|fraud)\b',  # possible confusion with "social justice" and "restorative justice",
    "Human rights and exploitation": r'\b((sex)? ?\-?traffic(k?ing)?|exploitation|forced labour|sex ?\-?workers?|prostitut(es?|ion))\b',
    "Inequality and discrimination": r'\b(inequality|discrimination|diversity|injustice|unjust|bias)\b',
    "Conflict and violence": r'\b(conflict|war|violence|combat)\b',
    "Accountability and fair trade": r'\b(fair ?-?trade|accountability|trade (fair|justice))\b',
    "Education and training": r'\b(schools?|pupils?|students?|school\-?age|teach(ers?|ing)|college|a ?\-?levels?|g\.?c\.?s\.?e\.?s?|key stage (1|2|3|one|two|three)|mentoring|educational|school(child|boy|girl)(ren|s)?|classroom)\b',  # need to exclude pre-school? schools are a venue for lots of activities
    "Personal development": r'\b(personal development|human capital|work-? ?life|self ?-?help)\b',
    "Employment": r'\b((un)?-?employ(ed|ment)|job-?seekers?|benefit claimants?|claim benefits|jobless|out of work)\b',
    "Children and young people": r'(child(ren)|junior|kids|young ?\-?(person|people|adults?)|youth|teen\-?agers?|adolescen(ce|ts)|juveniles?|puberty)',
    "Older people": r'\b(elderly|old(er)? ?\-?people|pensioners?|senior citizens?|(octo|nona)genarian|((second|2nd|1st|first) world war|WW(II|2)) veteran)\b',
    "Women and girls": r'\b(wom(e|a)n|girls?|lad(y|ies)|mothers?|females?|lesbians?)\b',
    "People from a specific ethnic background": r'\b(b\.?a?m\.?e\.?|black|ethnic|racial|roma)\b',  # black may be too generic?
    "People with a specific religious/spiritual beliefs": r'\b(christ(ian)?|muslim|jew(ish)|mosque|synagogue|church|buddhis(t|m)|sikh)\b',  # bit wide, need to exclude, eg church halls
    "People with a specific gender or sexual identity": r'\b(l\.?g\.?b\.?t?\.?q?\.?|lesbian|gay|bi\-?sexual|sexuality|sexual orientation|trans\-?(sexual|gender)?|homo\-?sexual|queer|cisgender|intersex)\b',  # rainbow - but children too
    "Minority or marginalised communities": r'\b(minorit(y|ies)|marginali(s|z)ed?|alienated|excluded|under-? ?represented|dis-? ?enfranchised)\b',
    "International and foreign affairs": r'\b((interational|foreign|direct|overseas) (aid|development))\b',
    "Migration, refugees and asylum seekers": r'\b(asylum ?-?seekers?|refugees?|migrants?|displaced persons?)\b',  # sanctuary?
    "Health and medicine": r'\b(healthy?|medicin(e|al)|well-?being|medical|illness(es)?|diseases?|fitness)\b',
    "Disability": r'\b(disabled|disabilit(ies|y)|blind(ness)?|deaf(ness)?|(hearing|sight) loss|amputee|wheel ?\-?chair|accessib(ility|le)|handicap(ped)?|less abled|sign language|impairment|visual(ly)? ?\-?impair(ment|ed))\b',
    'Learning disability': r'\b((learning|intellectual) (difficult|disabilit|disorder)(ies|y)?)\b',
    "Medical research": r'\b((clinical|medical) research|clinical trial|medicine|biochemistry|surgery|vaccine|biotechnology)\b',
    "Mental wellbeing, diseases and disorders": r'\b(mental ?\-?(health|illness(es)?|diseases?|disorders?)|depressian|schizophrenia|bi\-?polar|psychiatry|psychiatric|eating ?-?disorders?|Self ?\-?help|stress)\b',  # mental disease could cover dementia/learning disabilities
    "Physical wellbeing, diseases and disorders": r'\b(physical health|cancer|disease|illness|Down\'?s Syndrome|get fit|fitness|sport(ing|s)?|physiotherapy|Multiple Sclerosis|stroke|diabetes|Healthy Living|health ?care|blood pressure|virus|infection|nutrition|obesity)\b',  # exclude mental? often says "physical and mental health"
    "Palliative Care and Hospices": r'(hospices?|palliative|end ?-?of ? -?life)',
    "Addiction": r'\b(addict(ion)?|(alcohol|drug) abuse|alcohol(ism)?|drugs?|narcotics?|abstinence|dependenc(y|e)|amphetamine|nicotine|cocaine)\b',
    # "Public and societal benefit": r'',
    "Armed and rescue services": r'\b(armed forces|army|navy|air force|marines|armed services|(ex\-)?servicem(e|a)n\'?s?|veterans?|british legion|regiment(al)?|military|sailors?|soldiers?)\b',
    "Disaster preparedness and relief": r'\b(flood(s|ing)?|disasters?|rescue|survivors?|tsunami|storms?|hurricane|aftermath)\b',  # need a wider range "survivors" has DV use too, rescue used a lot for animals
    "Food and agriculture": r'\b(food|hunger|feed|local produce|food\-?bank|fruits?|vegetables?|cook(ery|ing)|famines?|(mal)?nutrition(ist)?|meat)\b',
    "Heritage and preservation": r'\b(heritage|preservation|estate|parks?|historic(al)?|museum|folklore|conservation|monuments?)\b',
    "Water, sanitation and public infrastructure": r'\b(water|sanitation|toilets?|sewage|hygien(e|ic)|wastewater)\b',  # need to exclude water sports
    "Public safety": r'\b(safety|security|risk)\b',
    "Science and technology": r'\b(scien(ce|tific|tist)s?|tech(nology|nical)?|engineer(ing)?|innovat(ion|e)|automation|computing)\b',
    "Technology": r'\b(tech(nology|nical)?|engineer(ing)?|innovat(ion|e))\b',
    "Scientific research": r'\b(scien(ce|tific|tist)s?|research)\b',
    # "Social welfare": r'\b()\b',
    "Crisis intervention": r'\b(crisis|trauma|anxiety|panic|cousell?(or|ing)|hotline)\b',
    "Family and relationships": r'\b(relationship|marriage|family breakdown|mediation|counselling|conflict resolution)\b',  # relationship a bit general
    "Housing and shelter": r'\b(housing|homeless(ness)?|tenants?|rough ?\-?sleep(ing|ers?)|runaways?|residents?|household|shelter)\b',  # housing is a verb, and is generic
    "Poverty": r'\b(poverty|deprivation|isolation|disadvantaged)\b',  # "poor" is too generic, used as an adjective
    "Isolation and loneliness": r'\b(isolat(ion|ed)|lonel(iness|y)|solitude|detachment|lonesome|solitary|alone)\b',
    "Domestic and sexual abuse": r'\b((domestic|sexual) (violence|abuse)|violence against women|honou?r killings?|child abuse)\b',
    "Care": r'\b(care ?\-?leavers?|leaving care|looked ?\-?after ?\-?(children)?|carers?|leave care)\b',  # definition of care here?
}

gender_regexes = {
    # the following identify genders
    "men": r'\b(m(e|a)n|boys?|fathers?|males?|lads?)\b',
    "women": r'\b(wom(e|a)n|girls?|lad(y|ies)|mothers?|females?|lesbians?)\b',
    "transgender": r'\b(trans\-?(sexual|gender)?)\b',
}

age_regexes = {
    # the following identify ages or life stages
    "baby": r'\b(bab(ies|y)|neo\-?nat(al|e)|childbirth|infants?|toddlers?|preschoolers?|newborn)\b',
    "children": r'\b(child(ren)|junior|kids)\b',
    "young-people": r'\b(young ?\-?people|youth|teen\-?agers?|adolescen(ce|ts)|juveniles?|puberty)\b',
    "adults": r'\b(adult)\b',
    "elderly": r'\b(elderly|old(er)? ?\-?people|pensioners?|senior citizens?|(octo|nona)genarian|((second|2nd|1st|first) world war|WW(II|2)) veteran)\b',
    "family": r'\b(famil(y|ies))\b',
}


# the selected age groups with their age ranges
age_categories = [
    {"label": "All ages", "age_from": 0, "age_to": 150},
    {"label": "Infants (0-3 years)", "age_from": 0, "age_to": 3},
    {"label": "Children (4-11 years)", "age_from": 4, "age_to": 11},
    {"label": "Adolescents (12-19 years)", "age_from": 12, "age_to": 19},
    {"label": "Young adults (20-35 years)", "age_from": 20, "age_to": 35},
    {"label": "Adults (36-50 years)", "age_from": 36, "age_to": 50},
    {"label": "Mature adults (51-80 years)", "age_from": 51, "age_to": 79},
    {"label": "Older adults (80+)", "age_from": 80, "age_to": 150}
]

# converting age beneficiaries to age ranges
age_bens = {
    "baby": (0, 3),
    "children": (4, 11),
    "young-people": (12, 25),
    "adults": (25, 65),
    "elderly": (65, 100)
}

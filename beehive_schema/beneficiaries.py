# beneficiary categories used
ben_categories = {
    "public": {
        "label": "The general public",
        "group": "People"
    },
    "crime": {
        "label": "Affected or involved with crime",
        "group": "People"
    },
    "relationship": {
        "label": "With family/relationship challenges",
        "group": "People"
    },
    "disabilities": {
        "label": "With disabilities",
        "group": "People"
    },
    "religious": {
        "label": "With specific religious/spiritual beliefs",
        "group": "People"
    },
    "disasters": {
        "label": "Affected by disasters",
        "group": "People"
    },
    "education": {
        "label": "In education",
        "group": "People"
    },
    "unemployed": {
        "label": "Who are unemployed",
        "group": "People"
    },
    "ethnic": {
        "label": "From a specific ethnic background",
        "group": "People"
    },
    "water": {
        "label": "With water/sanitation access challenges",
        "group": "People"
    },
    "food": {
        "label": "With food access challenges",
        "group": "People"
    },
    "housing": {
        "label": "With housing/shelter challenges",
        "group": "People"
    },
    "animals": {
        "label": "Animals and wildlife",
        "group": "Other"
    },
    "buildings": {
        "label": "Buildings and places",
        "group": "Other"
    },
    "mental": {
        "label": "With mental diseases or disorders",
        "group": "People"
    },
    "orientation": {
        "label": "With a specific sexual orientation",
        "group": "People"
    },
    "environment": {
        "label": "Climate and the environment",
        "group": "Other"
    },
    "physical": {
        "label": "With physical diseases or disorders",
        "group": "People"
    },
    "organisation": {
        "label": "This organisation",
        "group": "Other"
    },
    "organisations": {
        "label": "Other organisations",
        "group": "Other"
    },
    "poverty": {
        "label": "Facing income poverty",
        "group": "People"
    },
    "refugees": {
        "label": "Who are refugees and asylum seekers",
        "group": "People"
    },
    "services": {
        "label": "Involved with the armed or rescue services",
        "group": "People"
    },
    "care": {
        "label": "In, leaving, or providing care",
        "group": "People"
    },
    "exploitation": {
        "label": "At risk of sexual exploitation, trafficking, forced labour, or servitude",
        "group": "People"
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

# -*- coding: UTF-8 -*-

import re
from datetime import datetime

class Grant():
    """docstring for ."""

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
        "crime": r'\b(crim(inal|e)|justice|judicial|offenders?|custody|anti-social behaviour|prison(ers?)?|law centre|victim|murder|rape|theft|fraud)\b', # possible confusion with "social justice" and "restorative justice",
        "relationship": r'\b(relationship|marriage|family breakdown|mediation|counselling|conflict resolution)\b', # relationship a bit general
        "disabilities": r'\b(disabled|disabilit(ies|y)|blind(ness)?|deaf(ness)?|(hearing|sight) loss|amputee|wheel ?\-?chair|accessib(ility|le)|handicap(ped)?|less abled|sign language|impairment|visual(ly)? ?\-?impair(ment|ed))\b',
        "religion": r'\b(christ(ian)?|muslim|jew(ish)|mosque|synagogue|church|buddhis(t|m)|sikh)\b', # bit wide, need to exclude, eg church halls
        "disasters": r'\b(flood(s|ing)?|disasters?|rescue|survivors?|tsunami|storms?|hurricane|aftermath)\b', # need a wider range "survivors" has DV use too, rescue used a lot for animals
        "education": r'\b(schools?|pupils?|students?|school\-?age|teach(ers?|ing)|college|a ?\-?levels?|g\.?c\.?s\.?e\.?s?|key stage (1|2|3|one|two|three)|mentoring|educational|school(child|boy|girl)(ren|s)?|classroom)\b', # need to exclude pre-school? schools are a venue for lots of activities
        "unemployed": r'\b((un)?-?employ(ed|ment)|job-?seekers?|benefit claimants?|claim benefits|jobless|out of work)\b',
        "ethnic": r'\b(b\.?a?m\.?e\.?|black|ethnic|racial|roma)\b', # black may be too generic?
        "water": r'\b(water|sanitation|toilets?|sewage|hygien(e|ic)|wastewater)\b', # need to exclude water sports
        "food": r'\b(food|hunger|feed|local produce|food\-?bank|fruits?|vegetables?|cook(ery|ing)|famines?|(mal)?nutrition(ist)?|meat)\b',
        "housing": r'\b(housing|homeless(ness)?|tenants?|rough ?\-?sleep(ing|ers?)|runaways?|residents?|household|shelter)\b', # housing is a verb, and is generic
        "animals": r'\b(animals?|pets?|dogs?|cats?|horses?|wildlife|fauna|farm-animal|livestock|marine|habitat|birds?)\b',
        "buildings": r'\b((community|new|existing) building|built environment|architecture|refurbish(ing|ment)?|repairs?|restoration|(community|village) hall|Preservation Trust|Building works)\b', # building and heritage both a bit too wide
        "mental": r'\b(mental ?\-?(health|illness(es)?|diseases?|disorders?)|depressian|schizophrenia|bi\-?polar|psychiatry|psychiatric|eating ?-?disorders?|Self ?\-?help)\b', # mental disease could cover dementia/learning disabilities
        "orientation": r'\b(l\.?g\.?b\.?t?\.?q?\.?|lesbian|gay|bi\-?sexual|sexuality|sexual orientation|trans\-?(sexual|gender)?|homo\-?sexual|queer|cisgender|intersex)\b', # rainbow - but children too
        "environment": r'\b(environment(al)?|climat(e|ic)|global warming|carbon|energy efficien(t|cy)|ecosystem|nature|green spaces?|bio\-?diversity|sustainab(ility|le)|countryside|garden|pond|parks?|eco\-?audit|footpaths?|wilderness|greenhouse gas|ecolog(y|ical))\b', # environment a bti broad: learning environment, peaceful environment, etc
        "physical": r'\b(physical health|cancer|disease|illness|Down\'?s Syndrome|get fit|fitness|sport(ing|s)?|physiotherapy|Multiple Sclerosis|stroke|diabetes|Healthy Living|health ?care|blood pressure|virus|infection)\b', # exclude mental? often says "physical and mental health"
        "organisation": r'\b((this|our) organisation|core (costs|funding))\b', # not sure about this one!
        "organisations": r'\b(charities|local groups|community groups|social enterprises|Council for Voluntary Service|VCS)\b',
        "poverty": r'\b(poverty|deprivation|isolation|disadvantaged)\b', # "poor" is too generic, used as an adjective
        "refugees": r'\b(asylum ?-?seekers?|refugees?|migrants?|displaced persons?)\b', # sanctuary?
        "services": r'\b(armed forces|army|navy|air force|marines|armed services|(ex\-)?servicem(e|a)n\'?s?|veterans?|british legion|regiment(al)?|military|sailors?|soldiers?)\b',
        "care": r'\b(care ?\-?leavers?|leaving care|looked ?\-?after ?\-?(children)?|carers?|leave care)\b', # definition of care here?
        "exploitation": r'\b((sex)? ?\-?traffic(k?ing)?|exploitation|forced labour|sex ?\-?workers?|prostitut(es?|ion))\b',

        # the following are not in the original list
        "abuse": r'\b((domestic|sexual) (violence|abuse)|violence against women|honou?r killings?|child abuse)\b',
        "addiction": r'\b(addict(ion)?|(alcohol|drug) abuse|alcohol(ism)?|drugs?|narcotics?|abstinence)\b',
        "learning disabilities": r'\b((learning|intellectual) (difficult|disabilit|disorder)(ies|y)?)\b',

        # not really beneficiaries
        #"arts-culture": r'\b(arts?|theatre|music(al)?|museums?|galler(y|ies))\b',
        #"sport-recreation": r'\b(cricket|rugby|football|Tennis|swimming)\b',
        #"research": r'\b()\b',
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
        "baby": (0,3),
        "children": (4,11),
        "young-people": (12,25),
        "adults": (25,65),
        "elderly": (65,100)
    }

    # convert charity commission classification categories to beehive ones
    cc_to_beehive = {
        105: "poverty",
        108: "religious",
        111: "animals",
        203: "disabilities",
        204: "ethnic",
        205: "organisations",
        207: "public",
    }

    # convert OSCR classification categories to beehive ones
    oscr_to_beehive = {
        "No specific group, or for the benefit of the community": "public",
        "People with disabilities or health problems": "disabilities",
        "The advancement of religion": "religious",
        "People of a particular ethnic or racial origin": "ethnic",
        "The advancement of animal welfare": "animals",
        "The advancement of environmental protection or improvement": "environment",
        "Other charities / voluntary bodies": "organisations",
        "The prevention or relief of poverty": "poverty",
    }

    # fund names to replace when going through the data
    # for each funder you can either have
    # - a string (replace all with this),
    # - a dict (perform name replacement)
    # @todo - export to a separate file for easier editing
    swap_funds = {
        "Oxfordshire Community Foundation": "",
        "BBC Children in Need":{
            "zPositive Destinations": "Positive Destinations",
            "zFun and Friendship": "Fun and Friendship"
        },
        "Lloyds Bank Foundation for England and Wales": {
            "ZMSW - Community": "Community",
            "XA7 - Criminal Justice": "Criminal Justice",
            "XA1 - Community": "Community",
            "XA2 - Community": "Community",
            "XA12 - Community": "Community",
            "ZHNWL - Young Offenders": "Young Offenders",
            "Enable South": "Enable",
            "XA10 - Criminal Justice": "Criminal Justice",
            "ZSCSWL - Community": "Community",
            "ZKSEL - Young Offenders": "Young Offenders",
            "XA0 - Older People Programme": "Older People Programme",
            "XA4 - Criminal Justice": "Criminal Justice",
            "ZLNM - Community": "Community",
            "ZNWS - Community": "Community",
            "XA6 - Community": "Community",
            "XA7 - Community": "Community",
            "XA10 - Community": "Community",
            "ZHNWL - Community": "Community",
            "ZKSEL - Community": "Community",
            "XA9 - Criminal Justice": "Criminal Justice",
            "ZSWC - Community": "Community",
            "XA2 - Criminal Justice": "Criminal Justice",
            "XA11 - Community": "Community",
            "ZENEL - Community": "Community",
            "ZENEL - Young Offenders": "Young Offenders",
            "XA11 - Criminal Justice": "Criminal Justice",
            "XA5 - Community": "Community",
            "ZNEC - Community": "Community",
            "ZLarge Grants Programme": "Large Grants Programme",
            "ZNWM - Community": "Community",
            "Enable North": "Enable",
            "ZLNS - Community": "Community",
            "ZWMS - Community": "Community",
            "XA9 - Community": "Community",
            "ZEST - Community": "Community",
            "ZYKS - Community": "Community",
            "ZDCL - Community": "Community",
            "ZCSM - Community": "Community",
            "XA3 - Community": "Community",
            "XA6 - Criminal Justice": "Criminal Justice",
            "Invest South": "Invest",
            "XA8 - Community": "Community",
            "XA4 - Community": "Community",
            "Invest North": "Invest"
        },
        "Virgin Money Foundation": {
            "North East Fund 2016": "North East Fund",
            "North East Fund 2015": "North East Fund"
        },
        "LandAid Charitable Trust": {
            "Empty Properties Grants round 2015/16": "Empty Properties Grants",
            "Grants 2014/15": "Grants",
            "Open Grants round 2014/15": "Open Grants",
            "Project Sponsorship 2014/15": "Project Sponsorship",
            "Open Grants round 2013/14": "Open Grants",
            "Joint funding 2013/14": "Joint funding",
            "Open Grants round 2012/13": "Open Grants",
            "Joint Funding 2014/15": "Joint funding",
            "Project Sponsorship 2015/16": "Project Sponsorship",
            "Open Grants round 2015/16": "Open Grants",
        },
    }

    def __init__(self, grant, cdb):
        self.grant = self.clean_grant(grant)
        self.gender = "All genders"
        self.ages = []
        self.beneficiaries = []
        self.cdb = cdb  # charity database

    @staticmethod
    def clean_grant(grant):

        # set recipient details
        for k, r in enumerate(grant.setdefault("recipientOrganization", [{}])):
            for i in ["charityNumber", "companyNumber", "name", "url", "postalCode", "id"]:
                grant["recipientOrganization"][k].setdefault(i)
                if grant["recipientOrganization"][k][i] is not None:
                    grant["recipientOrganization"][k][i] = grant["recipientOrganization"][k][i].strip()

        return grant

    def get_desc(self):
        """
        Get the description field used for classification
        """
        return self.grant.get("title","") + " " + self.grant.get("description","")

    @staticmethod
    def parseCharityNumber(regno):
        """
        Clean a charity number so it can be searched for

        Also works for company numbers
        """
        if regno is None:
            return None
        regno = regno.strip().upper()
        regno = regno.replace('NO.', '')
        regno = regno.replace('GB-CHC-', '')
        regno = regno.replace('GB-COH-', '')
        regno = regno.replace(' ', '').replace('O', '0');
        if regno=="":
            return None
        return regno

    def get_charity(self, charityNumber):
        """
        Get information about a charity based on the charity number
        """
        charityNumber = self.parseCharityNumber(charityNumber)
        if charityNumber:
            return self.cdb.charities.find_one({"charityNumber": charityNumber, "subNumber": 0})

    def get_charity_beneficiaries(self, char = None):
        """
        Get a list of beneficiaries based on the charity's beneficiaries
        """
        beneficiaries = []

        if char is None:
            return beneficiaries

        # Charity Commission beneficiaries
        for c in char.get("class",[]):
            if c in self.cc_to_beehive:
                beneficiaries += self.cc_to_beehive[c]

        # OSCR beneficiaries
        for i in char.get("beta",{}):
            for c in char.get("beta",{})[i]:
                if c in self.oscr_to_beehive:
                    beneficiaries += self.oscr_to_beehive[c]

        return list(set(beneficiaries))

    @staticmethod
    def get_char_financial(char = None, time_from=None):
        """
        Financial information

        Retrieved either based on the latest available data (if time_from is
        None) or based on a date given.
        """
        financial = {
            "income": None,
            "spending": None,
            "employees": None,
            "volunteers": None
        }
        if char is None:
            return financial

        if time_from is None:
            time_from = datetime.now()

        # income and spending
        max_i = None
        use_i = None
        for i in char.get("financial", []):
            if i["income"] and i["spending"]:
                if time_from < i["fyEnd"] and time_from > i["fyStart"]:
                    use_i = i["fyEnd"]
                if max_i is None or i["fyEnd"] > max_i:
                    max_i = i["fyEnd"]

        if use_i is None:
            use_i = max_i

        for i in char.get("financial", []):
            if i["fyEnd"]==use_i:
                financial["income"] = i["income"]
                financial["spending"] = i["spending"]

        # volunteers and employees from part b
        max_i = None
        use_i = None
        for i in char.get("partB", []):
            if time_from < i["fyEnd"] and time_from > i["fyStart"]:
                use_i = i["fyEnd"]
            if max_i is None or i["fyEnd"] > max_i:
                max_i = i["fyEnd"]

        if use_i is None:
            use_i = max_i

        for i in char.get("partB", []):
            if i["fyEnd"]==use_i:
                financial["employees"] = i["people"]["employees"]
                financial["volunteers"] = i["people"]["volunteers"]

        # Less than £10k, £10k - £100k, £100k - £1m, £1m - £10m, £10m+, Unknown
        for i in ["income", "spending"]:
            if financial[i] is None:
                financial[i] = "Unknown"
            elif financial[i] < 10000:
                financial[i] = "Less than £10k"
            elif financial[i] < 100000:
                financial[i] = "£10k - £100k"
            elif financial[i] < 1000000:
                financial[i] = "£100k - £1m"
            elif financial[i] < 10000000:
                financial[i] = "£1m - £10m"
            elif financial[i] >= 10000000:
                financial[i] = "£10m+"
            else:
                financial[i] = "Unknown"

        #None, 1 - 5, 6 - 25, 26 - 50, 51 - 100, 101 - 250, 251 - 500, 500+, Unknown
        for i in ["employees", "volunteers"]:
            if financial[i] is None:
                financial[i] = "Unknown"
            elif financial[i] == 0:
                financial[i] = "None"
            elif financial[i] <= 5:
                financial[i] = "1 - 5"
            elif financial[i] <= 25:
                financial[i] = "6 - 25"
            elif financial[i] <= 50:
                financial[i] = "26 - 50"
            elif financial[i] <= 100:
                financial[i] = "51 - 100"
            elif financial[i] <= 250:
                financial[i] = "101 - 250"
            elif financial[i] <= 500:
                financial[i] = "251 - 500"
            elif financial[i] > 500:
                financial[i] = "500+"
            else:
                financial[i] = "Unknown"


        return financial

    @staticmethod
    def get_multi_national(char = None):
        """
        Work out if the charity operates across more than one country
        """
        if char is None:
            return None
        multi_national = False
        country_count = 0
        uk = False
        for i in char.get("areaOfOperation", []):
            if i["aooType"]=="D":
                country_count += 1
            elif i["aooType"]=="E":
                country_count += 2 # assume if it's a continent that it's more than one country
            else:
                uk = True
        if uk:
            country_count += 1
        if country_count > 1:
            multi_national = True
        return multi_national

    @staticmethod
    def get_operating_for(char, time_from = None):
        """
        Work out how long the recipient has been operating for

        @todo: when company data is available use the registration date as an alternative
        """
        if char is None:
            return -1

        if time_from is None:
            time_from = datetime.now()

        operating_fors = [
            ['Yet to start', 0],
            ['Less than 12 months', 1],
            ['Less than 3 years', 2],
            ['4 years or more', 3],
            ['Unknown', -1]
        ]

        reg_date = char.get("registration",[{}])[0].get("regDate")
        if reg_date is None:
            return -1
        time_operating = time_from - reg_date
        age = float(time_operating.days / 365)

        if age <= 1:
            return 1
        elif age <= 3:
            return 2
        else:
            return 3


    def get_company(self, companyNumber):
        """
        Get information about a company based on the company number

        Currently just says whether the company number is empty or not
        """
        companyNumber = self.parseCharityNumber(companyNumber)
        if companyNumber is not None and companyNumber!="":
            return True

    def get_company_from_charity(self, charity):
        """
        get a company number based on a charity record
        """
        return self.get_company(charity.get("mainCharity",{}).get("companyNumber"))

    def get_charity_from_company(self, companyNumber):
        """
        Try to find a charity based on a Company Number
        """
        companyNumber = self.parseCharityNumber(companyNumber)
        return self.cdb.charities.find_one({"mainCharity.companyNumber": companyNumber})

    def get_charity_and_company(self, charityNumber, companyNumber):
        """
        get information about a charity and company based on a recipient
        """
        char = None
        company = None

        # first check if a charity or company exists
        charity = self.get_charity(charityNumber)
        company = self.get_company(companyNumber)

        # if the charity exists but company doesn't, then check for company based on the charity
        if charity is not None and company is None:
            company = self.get_company_from_charity(charity)

        # if the company exists but the charity doesn't, check for charity based on the number
        if company is not None and charity is None:
            charity = self.get_charity_from_company(companyNumber)

        return (charity, company)

    def get_organisation_type(self, recipient):
        """
        Try to work out the best guess at an organisation type for a recipient

        @todo: match list to coded list in `beehive-data` and `beehive-giving` repositories
        """
        org_types = [
            "An individual",
            "An unregistered organisation OR project",
            "A registered charity",
            "A registered company",
            "A registered charity & company",
            "Another type of organisation"
        ]
        org_type = None
        name = recipient.get("name", "")
        charity = recipient.get("charity") or self.parseCharityNumber(recipient.get("charityNumber"))
        company = recipient.get("company") or self.parseCharityNumber(recipient.get("companyNumber"))
        if charity:
            if company:
                org_type = "A registered charity & company"
            else:
                org_type = "A registered charity"
        elif company:
            org_type = "A registered company"
        elif name=="This is a programme for individual veterans as opposed to organisaitons":
            org_type = "An individual"
        elif re.search(r'\b(school|college|university|council|academy|borough)\b', name, re.I):
            org_type = "Another type of organisation"
        else:
            org_type = "An unregistered organisation OR project"

        return org_type

    def fetch_recipients(self):
        """
        Fetch details about charity and company recipients, and guess organization type
        """
        grant_date = self.grant.get("awardDate")
        for k, r in enumerate(self.grant.setdefault("recipientOrganization", [{}])):
            # get charity and company details
            char_comp = self.get_charity_and_company( r.get("charityNumber"), r.get("companyNumber") )
            r["charity"] = char_comp[0]
            r["company"] = char_comp[1]

            # get charity beneficiaries
            r["beneficiaries"] = self.get_charity_beneficiaries(r["charity"])

            # get organisation type
            r["orgtype"] = self.get_organisation_type(r)
            if r["orgtype"]=="An individual":
                r["name"] = None

            # get financial details
            r.update( self.get_char_financial(r["charity"], grant_date) )

            # work out if multi national
            r["multi_national"] = self.get_multi_national(r["charity"])

            # work out the time operating_for
            r["operating_for"] = self.get_operating_for(r["charity"], grant_date)

            # get website url
            if (r["url"] is None or r["url"]=="") and r["charity"] is not None:
                r["url"] = r["charity"].get("mainCharity", {}).get("website")

            self.grant["recipientOrganization"][k] = r

    def get_grant_programme(self):
        """
        Get grant programme name
        """
        funder = self.grant.get("fundingOrganization", [{}])[0].get("name")
        grantProgramme = self.grant.get("grantProgramme", [{}])[0].get("title")
        if funder in self.swap_funds:
            if isinstance(self.swap_funds[funder], str):
                grantProgramme = self.swap_funds[funder]
            elif grantProgramme in self.swap_funds[funder]:
                grantProgramme = self.swap_funds[funder][grantProgramme]

        return grantProgramme

    @staticmethod
    def classify_grant(desc, regexes):
        """
        Use regexes to return a list of possible beneficiaries
        """
        return list(set([r for r in regexes if re.search(regexes[r], desc, re.I)]))

    @staticmethod
    def classify_grant_ages(desc):
        """
        Get an age range from a text string - something like "10-19 years old" or
        "aged 24-64".
        """
        agesre = r'\b(age(d|s)? ?(of|betweee?n)?|adults)? ?([0-9]{1,2}) ?(\-|to) ?([0-9]{1,2}) ?\-?(year\'?s?[ -](olds)?|y\.?o\.?)?\b'
        match = re.search(agesre, desc, re.I)
        if match:
            # only return if one of the age ranges has been included
            if match.group(1) or match.group(2) or match.group(3) or match.group(7) or match.group(8) or match.group(5)=="to":
                return (int(match.group(4)), int(match.group(6)))

    def age_to_category(self, ages):
        """
        turn an age produced by `classify_grant_ages` into a category
        """
        cats = {}
        for age in ages:
            for i in self.age_categories:
                if age[0] <= i["age_to"] and  i["age_from"] <= age[1] and i["label"]!="All ages":
                    cats[i["label"]] = i

        if len(cats)==0:
            for i in self.age_categories:
                if i["label"]=="All ages":
                    cats[i["label"]] = i

        return list(cats.values())

    def get_beneficiaries(self):
        """
        Get the list of beneficiaries for the grant, based on sources:
        - regex matches on name and description of grant
        - charity beneficiaries
        """
        bens = self.classify_grant( self.get_desc(), self.ben_regexes )
        for k, r in enumerate(self.grant.setdefault("recipientOrganization", [{}])):
            bens = bens + r.get("beneficiaries", [])

        self.beneficiaries = [{"name": b, "label": self.ben_categories[b]["label"], "group": self.ben_categories[b]["group"]} for b in bens if b in self.ben_categories]

    def get_affected(self):
        """
        Work out what is affected

        Using the list of beneficiaries work out whether it is people or others
        that are affected.
        """
        self.affect_people = False
        self.affect_other = False
        for b in self.beneficiaries:
            if b["group"]=="People":
                self.affect_people = True
            elif b["group"]=="Other":
                self.affect_other = True

    def get_ages(self):
        """
        Get the age ranges. Based on two sources:
        - looking for keywords in the name and description based on regexes
        - looking for strings like "5-16 years old" in the description
        """
        regex_ages = self.classify_grant( self.get_desc(), self.age_regexes )
        self.ages = [self.age_bens[b] for b in regex_ages if b in self.age_bens]

        age_category = self.classify_grant_ages( self.get_desc() )
        if age_category is not None:
            self.ages.append(age_category)

        self.ages = self.age_to_category(self.ages)

    def get_gender(self):
        """
        Work out the genders that are
        """
        regex_genders = self.classify_grant( self.get_desc(), self.gender_regexes )
        genders = []
        self.gender = "All genders"
        if "men" in regex_genders:
            genders.append("Male")
        if "women" in regex_genders:
            genders.append("Female")
        if "transgender" in regex_genders:
            genders.append("Transgender")
        if len(genders)==1:
            self.gender = genders[0]

    def process_grant(self):
        """
        Update the grant with the correct information
        """
        self.fetch_recipients()
        self.get_beneficiaries()
        self.get_affected()
        self.get_ages()
        self.get_gender()

    def beehive_output(self):
        """
        Turn the grant information into the right format for beehive-data

        Needs to be run after `process_grant`
        """
        grant = self.grant
        recipient = grant.get("recipientOrganization",[{}])[0]
        char = recipient.get("charity",{})
        beehive = {
            "publisher":            grant.get("dataset",{}).get("publisher",{}).get("name"),
            "license":              grant.get("dataset",{}).get("license"),
            "grant_identifier":     grant.get("id"),
            "funder_identifier":    grant.get("fundingOrganization",[{}])[0].get("id"),
            "funder":               grant.get("fundingOrganization",[{}])[0].get("name"),
            "fund":                 self.get_grant_programme(),
            "award_year":           int(grant["awardDate"][0:4]),
            "title":                grant.get("title"),
            "description":          grant.get("description"),
            "open_call":            grant.get("fromOpenCall")=="Yes",
            "approval_date":        grant.get("awardDate"),
            "planned_start_date":   grant.get("plannedDates",[{}])[0].get("startDate"),
            "planned_end_date":     grant.get("plannedDates",[{}])[0].get("endDate"),
            "currency":             grant.get("currency", "GBP"),
            "amount_awarded":       grant.get("amountAwarded"),
            "amount_applied_for":   grant.get("amountAppliedFor"),
            "amount_disbursed":     grant.get("amountDisbursed"),
            "type_of_funding":      None,
            "recipient": {
                "organisation_identifier":  recipient.get("id"),
                "country":                  "GB",
                "organisation_type":        recipient.get("orgtype"),
                "name":                     recipient.get("name"),
                "charity_number":           recipient.get("charityNumber"),
                "company_number":           recipient.get("companyNumber"),
                "organisation_number":      None,
                "city":                     None,
                "region":                   None,
                "postal_code":              recipient.get("postalCode"),
                "website":                  recipient.get("url"),
                "multi_national":           recipient.get("multi_national"),
            },
            "operating_for":            recipient.get("operating_for"),
            "income":                   recipient.get("income"),
            "spending":                 recipient.get("spending"),
            "employees":                recipient.get("employees"),
            "volunteers":               recipient.get("volunteers"),
            "beneficiaries":{
                "affect_people": self.affect_people,
                "affect_other":  self.affect_other,
                "genders":       self.gender,
                "ages":          self.ages,
                "beneficiaries": self.beneficiaries
            },
            "locations": {
                "geographic_scale": "",
                "country": [
                    {"country": "", "areas": []}
                ]
            }
        }

        return beehive

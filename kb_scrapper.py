# -*- coding: utf-8 -*-

#
# EECS 371
# Term Project
# Travel Recommender
#
# Scraper to create knowledge base for Travel Recommender
#

from SPARQLWrapper import SPARQLWrapper, JSON
import urllib2
import html2text
from math import sin, cos, sqrt, atan2, radians
from bs4 import BeautifulSoup

# list of categories/attributes
attributes = [
    # mountain
    'trekking', 'climbing', 'skiing', 'snowboarding', 'snowshoeing', 'canyon', 'cave',
    # water
    'diving', 'rafting', 'sailing', 'snorkel', 'surfing', 'fishing', 'kayak', 'swimming', 'beach',
    # forest
    'hiking', 'camping', 'birdwatching', 'hunting',
    # cultural
    'museum', 'historical place', 'castle', 'nightlife', 'vineyard', 'beer',
    # recreational
    'biking', 'golf', 'safari', 'sandboarding', 'zipline'
    ]

class CountryInfo:
    """
    Holds information about country as travel destination
    """
    def __init__(self):
        self.name = ""
        self.capital = ""
        self.lat = 0
        self.lng = 0
        self.descr = ""
        self.attributes = []

    def __str__(self):
        return self.name + " (" + self.capital + ")"

    def __repr__(self):
        return self.name + " (" + self.capital + ")"


def queryCountriesList():
    """
    Fetches information about countries, capitals, geo coordinates, abstract tourism description
    from dbpedia.org using SPARQL
    :return: dictionary of countries
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    print 'Fetching list of countries from dbpedia.org...'
    sparql.setQuery("""
        SELECT DISTINCT ?country, ?country_name, ?capital, ?capital_name, ?lat, ?lng
        WHERE { 
                { ?country rdf:type yago:WikicatMemberStatesOfTheUnitedNations }
                { ?country rdfs:label ?country_name }
                { ?country dbo:capital ?capital }
                { ?capital rdfs:label ?capital_name }
                OPTIONAL { ?capital geo:lat ?lat }
                OPTIONAL { ?capital geo:long ?lng }
                FILTER (lang(?capital_name) = 'en')
                FILTER (lang(?country_name) = 'en')
               }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    countries = {}
    for result in results["results"]["bindings"]:
        info = CountryInfo()
        info.name = result["country_name"]["value"].encode('ascii', 'ignore')
        info.capital = result["capital_name"]["value"].encode('ascii', 'ignore')
        if "lat" in result:
            info.lat = float(result["lat"]["value"].encode('ascii', 'ignore'))
            info.lng = float(result["lng"]["value"].encode('ascii', 'ignore'))

        # skip duplicates
        if info.name not in countries:
            countries[info.name] = info
    print "Fetched", len(countries), "countries"
    return countries


def queryCityCoordinates(city):
    """
    Query city coordinates from dbpedia.org using SPARQL
    :param city: 
    :return: 
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    sparql.setQuery("""
            SELECT * WHERE {
             {?city rdfs:label \"""" + city + """\"@en}
             {?city a dbo:Place }
             {?city geo:lat ?lat}
             {?city geo:long ?long}
            }
        """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    countries = {}
    for result in results["results"]["bindings"]:
        return (float(result["lat"]["value"]), float(result["long"]["value"]))

    return (0, 0)


def findAttributesInText(text):
    country_attrs = []
    for attr in attributes:
        if attr in text:
            country_attrs.append(attr)
    return country_attrs


def getCountryAttributes(country):
    """
    Analyze country attributes using webpage on wiktravel.org
    :param country: 
    :param attributes: 
    :return: 
    """

    country_attrs = []

    try:
        url = "https://wikitravel.org/en/" + country
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}

        print '\t',url
        page = urllib2.urlopen(urllib2.Request(url, headers=hdr))
        soup = BeautifulSoup(page, "html.parser")
        text = html2text.html2text(soup.text).lower()
        country_attrs = findAttributesInText(text)

        # scan for other destinations links
        links = []
        result = soup.find("span", {"id": "Other_destinations"})
        if result:
            result = result.parent
            result = result.find_next_sibling("ul")
            if result:
                resultlist = result.find_all("li")
                for i in resultlist:
                    des = i.find("a")
                    if des and 'href' in des.attrs:
                        links.append(des.attrs['href'])

        for link in links:
            try:
                url = "https://wikitravel.org" + link
                print '\t', url
                page = urllib2.urlopen(urllib2.Request(url, headers=hdr))
                soup = BeautifulSoup(page, "html.parser")
                text = html2text.html2text(soup.text).lower()
                page_attrs = findAttributesInText(text)
                for i in page_attrs:
                    if i not in country_attrs:
                        country_attrs.append(i)
            except urllib2.HTTPError:
                pass
            except urllib2.URLError:
                pass


    except urllib2.HTTPError:
        pass
    except urllib2.URLError:
        pass
    return country_attrs


def distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two coordinates on earth
    :return: distance in km
    """
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lng1)
    lat2 = radians(lat2)
    lon2 = radians(lng2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def distanceToStr(dist):
    s = []
    if dist < 110000:
        s.append('long haul')
    if dist < 11000:
        s.append('full day')
    if dist < 6000:
        s.append('half day')
    if dist < 4000:
        s.append('few hours')
    if dist < 2000:
        s.append('close')
    return s


def writeKnowldgeBaseFile(countries):
    """
    Write information about countries as knowledge base for prolog file
    :param countries: 
    """
    file = open("kb.pl", "w")
    file.write("%\n")
    file.write("% Knowledge base for travel suggester\n")
    file.write("%\n\n")

    for country in countries:
        file.write("distance('"+country+"', \""+str(int(countries[country].distance))+" km\").\n")
    file.write("\n\n")

    file.write("%\n% Attributes for places\n%\n")
    for country in countries:
        for attr in countries[country].attributes:
            file.write("has('" + country + "',activity,'"+attr+"').\n")
        # add distance
        distances = distanceToStr(countries[country].distance)

        for d in distances:
            file.write("has('" + country + "',distance,'" + d + "').\n")
        file.write('\n')

    file.close()


if __name__ == "__main__":
    # query list of countries from dbpedia
    countries = queryCountriesList()

    # query coordinates of Chicago from dbpedia
    lat, lng = queryCityCoordinates("Chicago")

    # calculate distance (km) to each capital
    for country in countries:
        countries[country].distance = distance(lat, lng, countries[country].lat, countries[country].lng)

    # query attributes from wikitravel.org
    for country in sorted(countries.keys()):
        print 'Analyzing travel information for', country
        countries[country].attributes = getCountryAttributes(country)

    for country in countries:
        print country, "(", countries[country].capital, ",", countries[country].distance, "): ", ", ".join(countries[country].attributes)

    # write KB file
    writeKnowldgeBaseFile(countries)
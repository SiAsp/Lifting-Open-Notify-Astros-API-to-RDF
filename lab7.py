import json
import owlrl
import requests
import spotlight

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF
from spotlight import SpotlightException

# People in space API
API_URL = "http://api.open-notify.org/astros.json"

# Spotlight
SERVER = "https://api.dbpedia-spotlight.org/en/annotate"
CONFIDENCE = 0.5

# Namespaces
ex = Namespace("https://example.org/")
dbr = Namespace("http://dbpedia.org/resource/")
dul = Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
schema = Namespace("http://schema.org/")
wd = Namespace("http://www.wikidata.org/entity/")


class SpaceGraph(Graph):
	""" Class-handler for the People in Space API """
	def __init__(self):
		# Initialise super to be able to use the regular RDFLib graph attributes
		super().__init__()
		self.astronauts = []

	@staticmethod
	def get_updated_list():
		""" Retrieves an updated list of astronauts and their craft """
		r = requests.get(API_URL)
		json_data = json.loads(r.text)
		return json_data

	@staticmethod
	def annotate_entity(entity, filters={"types": "DBpedia:Astronaut"}):
		""" Uses DBpedia Spotlight to annotate a string with a corresponding DBpedia resource and its types """
		try:
			annotations = spotlight.annotate(SERVER, entity, confidence=CONFIDENCE, filters=filters)
			# Format: [{'URI': 'http://dbpedia.org/resource/Bergen', 'support': 9672, 'types': 'Wikidata:Q515,Wikidata:Q486972,Schema:Place,Schema:City,DBpedia:Settlement,DBpedia:PopulatedPlace,DBpedia:Place,DBpedia:Location,DBpedia:City', 'surfaceForm': 'Bergen', 'offset': 0, 'similarityScore': 0.9997191614945689, 'percentageOfSecondRank': 0.000135980236683039}]
			# Here we only need to care about the URI and types.
		# This will trigger if no resource is found
		except SpotlightException as e:
			print(e)
			# Use dummy-values we know are correct. This follows the same format as the response from Spotlight, and allows us to use the same parser-method (add_annotations, add_astronaut) for both
			annotations = [{
				"URI": ex + entity.replace(" ", "_"),
				"types": "DBpedia:Astronaut"
			}]
		return annotations

	def add_annotations(self, annotations, craft):
		""" Adds all given annotations to the graph """
		annotated_craft_URI = self.add_craft(craft)
		# Spotlight wil return all entities matching the criteria. This will be a sorted list of a dict representing each entity. Here we add all matches to the graph, but we could alternatively only add the first.
		for annotation in annotations:
			self.add_astronaut(annotation, annotated_craft_URI)

	def add_astronaut(self, annotation, annotated_craft):
		""" Adds a given annotation to the graph, i.e. adds the astronaut and craft to the graph, with metadata """
		self.add((URIRef(annotation["URI"]), ex.onCraft, URIRef(annotated_craft)))
		self.add_metadata(annotation)
		if "DBpedia:Astronaut" in annotation["types"]:
			self.astronauts.append(annotation["URI"])
	
	def add_craft(self, craft):
		annotation = self.annotate_entity(craft, filters={})[0]
		self.add_metadata(annotation)
		return annotation["URI"]


	def add_metadata(self, annotation):
		""" Adds the types of an annotation to the graph """
		types = annotation["types"].split(",")
		'Wikidata:Q515,Wikidata:Q486972,Schema:Place,Schema:City,DBpedia:Settlement,DBpedia:PopulatedPlace,DBpedia:Place,DBpedia:Location,DBpedia:City'
		entity = URIRef(annotation["URI"])
		for _type in types:
			if "dbpedia" in _type.lower():
				self.add((entity, RDF.type, URIRef(dbr + _type.split(":")[1])))
			elif "wikidata" in _type.lower():
				self.add((entity, RDF.type, URIRef(wd + _type.split(":")[1])))
			elif "schema" in _type:
				self.add((entity, RDF.type, URIRef(schema + _type.split(":")[1])))
			elif "FOAF" in _type:
				self.add((entity, RDF.type, URIRef(FOAF + _type.split("/0.1/")[1])))
			elif "DUL" in _type:
				self.add((entity, RDF.type, URIRef(dul + _type.split(":")[1])))
		
	def add_astronaut_relations(self):
		""" Adds a foaf:knows relation between all astronauts. This does not take the craft they are on into account - could be improved. """
		for astronaut in self.astronauts:
			for friend in self.astronauts:
				if astronaut != friend:
					self.add((URIRef(astronaut), FOAF.knows, URIRef(friend)))

	def create_graph(self):
		""" Gets the updated list of astronauts and adds them to the graph """
		data = self.get_updated_list()
		for record in data["people"]:
			annotations = self.annotate_entity(record["name"])
			self.add_annotations(annotations, record["craft"])
		self.add_astronaut_relations()

if __name__ == '__main__':
	g = SpaceGraph()
	g.bind("ex", ex)
	g.bind("dbr", dbr)
	g.bind("dul", dul)
	g.bind("foaf", FOAF)
	g.bind("wd", wd)
	g.create_graph()

	context = {
		"ex": str(ex),
		"dbr": str(dbr),
		"onCraft": str(ex.onCraft),
		"knows": str(FOAF.knows)
	}
	g.serialize("lab7/data.json", format="json-ld", context=context)
	g.serialize("lab7/data.ttl", format="ttl")
# Tasks

## Task 1 
Write a small program that queries the Open Notify Astros API (link below) for the people currently in space. Create a graph from the response connecting each Astronaut to the craft they are currently on, for instance using http://example.com/onCraft as a property. Also as the space station is not too big, it is safe to assume that two people spent who time on it at the same time know each other, so add this to the graph.

* Astros API url: http://api.open-notify.org/astros.json
* Documentation: http://open-notify.org/Open-Notify-API/People-In-Space/

## Task 2
Serialise the graph to JSON-LD format, set the context of the JSON-LD object to represent the properties for knows and onCraft.

First you need to pip install the json-ld portion of rdflib if you have not already:
```bash
pip install rdflib-jsonld
```
## If you have more time 

Build upon the program using the DBpedia Spotlight API (example code below) to use a DBpedia-resource in your graph if one is available. You can add some simple error-handling for cases when no DBpedia resource is found - use an example-entity in stead. Keep in mind that some resources may represent other people with the same name, so try to change the types-parameter so you only get astronauts in return, the confidence-parameter might also help you with this.

The response from DBpedia Spotlight is a list of dictionaries, where each dictionary contains the URI of the resource, its types and some other metadata we will not use now. Set the type of the resouce to the types listed in the response.

### Example code for DBpedia Spotlight query
First:
```
pip install pyspotlight
```
Then:
```py
import spotlight

SERVER = "https://api.dbpedia-spotlight.org/en/annotate"
annotations = spotlight.annotate(SERVER, "str_to_be_annotated")
```
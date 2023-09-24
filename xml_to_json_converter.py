#!python -m spacy download de_core_news_sm
#%%Imports
from bs4 import BeautifulSoup as bs
from bs4.formatter import XMLFormatter
import bs4
import json 
import spacy
import spacy
from spacy.lang.de.examples import sentences 
import re
nlp = spacy.load("de_core_news_sm")

xmlFormatter = XMLFormatter(indent=4)

#%%
content = []
xmlFileSoups = []
pdfsPath = ["xmlFiles/1-14_Einleitung_enriched.xml",
"xmlFiles/15-43_Personenrecht_allgemein_enriched.xml",
"xmlFiles/44-100_Eherecht_allgemein_enriched.xml",
"xmlFiles/285-308_Sachbegriff_enriched.xml",
"xmlFiles/309-352_Besitz_enriched.xml",
"xmlFiles/353-379_Eigentum_enriched.xml",
"xmlFiles/380-403_Aneignung_enriched.xml",
"xmlFiles/404-422_Zuwachs_enriched.xml",
"xmlFiles/423-446_Erwerb_durch_Übergabe_enriched.xml",
"xmlFiles/447-471_Pfandrecht_I_enriched.xml",
"xmlFiles/472-530_Dienstbarkeiten_enriched.xml",
"xmlFiles/825-858_Miteigentum_enriched.xml",
"xmlFiles/859-864a_Vertraege_und_ Rechtsgeschaefte_allgemein_I_enriched.xml",
"xmlFiles/865-880a_Vertraege_allgemein_II_enriched.xml",
"xmlFiles/881-916_Vertraege_enriched.xml",
"xmlFiles/917-937_Allgemeine_Bestimmungen_enriched.xml",
"xmlFiles/938-955_Schenkung_enriched.xml",
"xmlFiles/957-970c_Verwahrung_enriched.xml",
"xmlFiles/971-982_Leihe_enriched.xml",
"xmlFiles/983-1001_Darlehen_enriched.xml",
"xmlFiles/1002-1034_Bevollmaechtigungsvertrag_enriched.xml",
"xmlFiles/1035-1044_Geschaeftsfuehrung_ohne_Auftrag_enriched.xml",
"xmlFiles/1045-1052_Tausch_enriched.xml",
"xmlFiles/1053-1089_Kauf_enriched.xml",
"xmlFiles/1172-1174_Verlagsvertrag, Unerlaubtheitskondiktion_enriched.xml",
"xmlFiles/1267-1292_Gluecksvertraege_enriched.xml",
"xmlFiles/1342-1367_Buergschaft_enriched.xml",
"xmlFiles/1368-1374_Pfandrecht_II_enriched.xml",
"xmlFiles/1375-1391_Novation_und_Vergleich_enriched.xml",
"xmlFiles/1392-1399_Zession_enriched.xml",
"xmlFiles/1400-1410_Anweisung_Schulduebernahme_enriched.xml",
"xmlFiles/1411-1430_Aufhebung_der_Rechte_I_enriched.xml",
"xmlFiles/1431-1450_Aufhebung_der_Rechte_II_enriched.xml",
"xmlFiles/1451-1477_Verjährung_und_Ersitzung_enriched.xml"
]
for path in pdfsPath:     
    # Read the XML file
    print(path)
    with open(path, "r", encoding="utf8") as file:
        content = file.readlines()
        content = "".join(content)
        bs_content = bs(content, "xml")
        xmlFileSoups.append(bs_content)
        


#%%

def cleanXmlFromNotesAndIdno(xmlElement):
    if xmlElement.idno:
        for idno in xmlElement.findAll("idno"):
            idno.decompose()
    if xmlElement.note: 
       for note in xmlElement.findAll("note"):
        note.decompose()
        
def tranformTextWithStripAndSpacy(nlp, text):
    textBlock = text.text.strip()
    sents = list(nlp(textBlock).sents)
    sents = [str(sent).strip() for sent in sents]
    sents = [re.sub(' +', ' ', sent) for sent in sents]
    return sents

def flatten(l:list):
    return [item for sublist in l for item in sublist]

#%%   
paragraphs =[]
for xmlSoup in xmlFileSoups:    
    result = xmlSoup.findAll("div", {"ana": "akn:paragraph"}) 
    for paragraph in result:
        #get paragraph number from xml
        translation_table = dict.fromkeys(map(ord, '§.'), None)
        paragraphNumber = paragraph.get('n').translate(translation_table)
        
        #get Original and Alternative texts without notations
        textObjects = paragraph.find("choice").findAll("seg", {"ana": "akn:p"})
        paragraph = {}
        paragraph['paragraphNumber'] = paragraphNumber
        
        standardCase = False
        
        for text in textObjects: 
            cleanXmlFromNotesAndIdno(text)
            paragraphTypeName = text.get('type').replace('eabgb:', '')
            paragraph[paragraphTypeName] = []
            
            if text.find("seg", {"type": "eabgb:absatz"}) and standardCase == False:    
                
                subparagraphs = text.findAll("seg", {"type": "eabgb:absatz"})
                for subparagraph in subparagraphs:
                    translation_table_sub = dict.fromkeys(map(ord, '()'), None)
                    subparagraphNumber = subparagraph.get('n').translate(translation_table_sub)
                    
                    if subparagraph.find("s", {"type": "eabgb:satz"}):
                        sentences = subparagraph.findAll("s", {"type": "eabgb:satz"})
                        sentences = [tranformTextWithStripAndSpacy(nlp,sentence) for sentence in sentences]
                        sentences = flatten(sentences)
                        paragraph[paragraphTypeName].append({
                                                            "subparagraphNumber": subparagraphNumber, 
                                                            "sentences":sentences
                                                })    
                    else: 
                        sentences = tranformTextWithStripAndSpacy(nlp,subparagraph)
                        paragraph[paragraphTypeName].append({
                                                            "subparagraphNumber": subparagraphNumber, 
                                                            "sentences":sentences
                                                })
                
                                                        
            elif text.find("s", {"type": "eabgb:satz"}) and standardCase == False:
                sentences = text.findAll("s", {"type": "eabgb:satz"}) 
                
                for i, sentence in enumerate(sentences):
                    
                    sentence = tranformTextWithStripAndSpacy(nlp,sentence)
                    paragraph[paragraphTypeName].append({
                                                        "subparagraphNumber": i+1, 
                                                        "sentences": sentence
                                                })  
            
            else:
                if paragraphTypeName == "originaltext": 
                    standardCase = True
                
                sents = tranformTextWithStripAndSpacy(nlp, text)
                paragraph[paragraphTypeName].append({
                                                    "subparagraphNumber": 1, 
                                                    "sentences": sents
                                                })    
        if not (paragraph["originaltext"][0]["sentences"] == []):
            paragraphs.append(paragraph)
        

# %%
abgbFile = open("abgb.json", "w")
# magic happens here to make it pretty-printed
abgbFile.write(json.dumps(paragraphs, indent=4))
abgbFile.close()
# %%

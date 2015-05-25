#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import revisionprocessor

def snaktotext(snak) :
	if snak[0] == 'value' :
		if snak[2] == 'wikibase-entityid' :
			return 'P' + str(snak[1]) + ' Q' + str(snak[3]['numeric-id'])
		elif snak[2] == 'string' :
			return 'P' + str(snak[1]) + ' {' + snak[3] + '}'
		elif snak[2] == 'time' :
			return 'P' + str(snak[1]) + ' ' + str(snak[3])
		elif snak[2] == 'globecoordinate' :
			return 'P' + str(snak[1]) + ' ' + str(snak[3])
		else :
			print snak
			return 'P' + str(snak[1]) + ' *'
			exit()
	elif snak[0] == 'somevalue' :
		return 'P' + str(snak[1]) + ' +'
	elif snak[0] == 'novalue' :
		return 'P' + str(snak[1]) + ' -'
	else :
		print snak
		return 'P' + str(snak[1]) + ' *'
		exit()

# Based on the latest version of a page write out the 
# Knowledge Base file to kb.txt
class RPKB(revisionprocessor.RevisionProcessor):
	def __init__(self,helper,output,maxdate=''):
		self.helper = helper
		self.output = output
		self.curMaxRev = -1
		self.curMaxTimestamp = False
		self.curMaxRawContent = False
		self.curRevsFound = 0
		self.maxDate = maxdate

		self.descSize = 0
		self.claimSize = 0
		self.labelSize = 0
		self.aliasSize = 0
		self.linkSize = 0

	def startPageBlock(self,title,isItem,isNew):
		revisionprocessor.RevisionProcessor.startPageBlock(self,title,isItem,isNew)
		self.curMaxRev = -1
		self.curMaxTimestamp = False
		self.curMaxRawContent = False

	def processRevision(self,revId,timestamp,user,isIp,rawContent):
		if self.isNew and self.curMaxRev < int(revId) :
			if self.maxDate == '' or self.maxDate > timestamp:
				self.curMaxRev = int(revId)
				self.curMaxTimestamp = timestamp
				self.curMaxRawContent = rawContent

	def endPageBlock(self):
		if self.curMaxRev >= 0:
			self.curRevsFound += 1
			val = self.helper.getVal(self.curMaxRev,self.curMaxRawContent)
			id = int(self.curTitle[1:])

			newdesc_str = str(self.__reduceDictionary(val['description'],('en')))
			newlabel_str = str(self.__reduceDictionary(val['label'],('en')))
			newaliases_str = str(self.__reduceDictionary(val['aliases'],('en')))
			newclaims_str = str(self.__reduceClaims(val['claims']))
				

		#	print newclaims_str
	#		exit

			self.descSize += len(newdesc_str)
			self.claimSize += len(newclaims_str)
			self.labelSize += len(newlabel_str)
			self.aliasSize += len(newaliases_str)

			if self.isItem:
				links_str = str(val['links'])
				self.linkSize += len(links_str)
			self.__write(id, val)

		revisionprocessor.RevisionProcessor.endPageBlock(self)

	# writes an item in KB syntax to the output file
	def __write(self,id, val):
		#print val
		#exit
		title = 'Q' + str(id)
		if 'datatype' in val :
			title = 'P' + str(id)
			self.output.write(title + ' type ' + val['datatype'] + " .\n")
		if 'label' in val :
			if len(val['label']) > 0 :
				for lang in val['label'].keys() :
					self.output.write(u'' + title + ' label {' + lang + ':' + val['label'][lang] + "} .\n")
		if 'description' in val:
			if len(val['description']) > 0 :
				for lang in val['description'].keys() :
					self.output.write(u'' + title + ' description {' + lang + ':' + val['description'][lang] + "} .\n")
		if 'links' in val :
			if len(val['links']) > 0 :
				for lang in val['links'].keys() :
					#print title
					#print lang
					#print val['links'][lang]
					if type(val['links'][lang]) is dict :
						name = val['links'][lang]['name']
					else :
						name = val['links'][lang]
					#print name
					self.output.write(u'' + title + ' link {' + lang + ':' + name + "} .\n")
		if 'aliases' in val :
			if len(val['aliases']) > 0 :
				for lang in val['aliases'].keys() :
					for alias in val['aliases'][lang] :
						#print alias
						self.output.write(u'' + title + ' alias {' + lang + ':' + alias.get('value') + "} .\n")
		if 'c-laims' in val :
			#print val['claims']
			#exit
			if len(val['claims']) > 0 :
				for pval,claims in val['claims'].items() :
					quals = ''
					print pval
					print claims
					if ( len(claim['q']) + len(claim['refs'])) > 0 :
						if (len(claim['q']) > 0) :
							for q in claim['q'] :
								quals += '  ' + snaktotext(q) + " ,\n"
						if (len(claim['refs']) > 0) :
							for ref in claim['refs'] :
								quals += "  reference {\n"
								for r in ref :
									quals += '    ' + snaktotext(r) + " ,\n"
								quals += "  },\n"
						quals = " (\n" + quals + ' )'
							
					snak = snaktotext(claim['m'])
					self.output.write(u'' + title + ' ' + snak + quals + " .\n")

	# Truncate values of some keys in a dictionary to save space
	def __reduceDictionary(self,data,preserveKeys):
		newdata = {}
		for key in data:
			if key in preserveKeys:
				newdata[key] = data[key]
			else:
				newdata[key] = 1
		return newdata

	# Simplify claim structure to save space
	def __reduceClaims(self,claims):
		newclaims = []
		for p,claim in claims.items():

			#newclaim = claim.copy()
			#newclaim = dict(zip(claim[0::2], claim[1::2]))
			#newclaim = list(claim)
			newclaim = claim.pop()
			#newclaim['q'] = dict()	
			
	#		newclaim['q'] = {}
			if 'qualifiers' in newclaim:
				newclaim['q'] = newclaim.pop('qualifiers')
			
			newclaim['m'] = newclaim.pop('mainsnak')
			
			if 'references' in newclaim:
				newclaim['refs'] = newclaim.pop('references')

			#newclaim.pop('q')

			newclaim['m'] = self.__reduceSnak(newclaim['m'])

			if newclaim['rank'] == 1:
				newclaim.pop('rank')

			newqualifiers = []
			hasQ = False
			#print newclaim
			if 'q' in newclaim:
				for snak in newclaim['q']:
					snakList = newclaim['q']
					hasQ = True
					#print snakList.items()
					#exit
					for somerandvalue,snaks in snakList.items():
						for snak in snaks:
					

							if 'qualifiers-order' not in snak:
				#				print snak
								newqualifiers.append(self.__reduceSnak(snak))
			
				if hasQ:
					newclaim['q'] = newqualifiers
				else:
					newclaim.pop('q')

			newrefs = []
			hasRef = False
			
			#TODO SAME AS ABOVE HERE
			if 'refs' in newclaim:
				for ref in newclaim['refs']:
					hasRef = True
					newref = []
					#print ref
					#print "\n"
					#for blub,snak in ref:
						#print snaks
					#	for snak in snaks:
							#print snak
					#	print snak
					
					snaks = ref.pop('snaks')
					#print snaks
					
					for somepval,snakList in snaks.items():
						for snak in snakList:


							if 'snaks-order' not in ref:	
								newref.append(self.__reduceSnak(ref))
					newrefs.append(newref)
				if hasRef:
					newclaim['refs'] = newrefs
				else:
					newclaim.pop('refs')

			newclaims.append(newclaim)
		return newclaims

	def __reduceSnak(self,snak):

		#print snak
		#print "\n"

	#	if snak = {}:
	#		print snaki
		#if 'datavalue' in snak:
		snak[0] = snak.get('snaktype')
		snak[1] = snak.get('property')
		#print snak
		#print "\n"


		if 'datavalue' in snak:
			snak[2] = snak.get('datavalue').pop('type')
			snak[3] = snak.get('datavalue').pop('value')
	
			snak.pop('datavalue')

		if snak[0] == 'value':
			if snak[2] == 'wikibase-entityid':
				if snak[3]['entity-type'] == 'item':
					return ('R',snak[1],snak[3]['numeric-id'])
			if snak[2] == 'string':
				return ('S',snak[1],snak[3])
			if snak[2] == 'time':
				return ('T',snak[1],snak[3]['precision'],snak[3]['time'],snak[3]['timezone'],snak[3]['calendarmodel'][35:],snak[3]['after'],snak[3]['before'])

		# Fallback:
		return tuple(snak)

	def logReport(self):
		logging.log('     * Number of latest revisions found: ' + str(self.curRevsFound))
		logging.log('     * Size used for latest revs (in chars): claims: ' + str(self.claimSize) + ', aliases: ' + str(self.aliasSize) + ', labels: ' + str(self.labelSize) + ', links: ' + str(self.linkSize) + ', descs: ' + str(self.descSize))


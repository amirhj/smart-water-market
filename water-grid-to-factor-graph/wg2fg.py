import json, sys

wg = json.loads(open(sys.argv[1], 'r').read())
time_step = int(sys.argv[2])
fg = {'variables':[], 'functions': [], 'constants': []}
func = open('functions.py', 'w')

func.write("""import math

class Functions:
	def __init__(self, fg):
		self.fg = fg

	def calculate(self, name, values):
		function = getattr(self, name)
		return function(values)
""")

fg['constants'].append({'name': 'price', 'value': wg['prices'][time_step]})
fg['constants'].append({'name': 'accuracy', 'value': wg['accuracy']})

for p in wg['pipelines']:
	name = 'w_%s_%s' % (p['from'], p['to'])
	fg['variables'].append({'name': name, 'domain':{'min':0, 'max': 400, 'step': 1}})

	name = 'tp_%s_%s' % (p['from'], p['to'])
	fg['constants'].append({'name': name, 'value':float(p['transfer_price'])})

for a in wg['agents']:
	name = 'max_delivery_%s' % a['name']
	fg['constants'].append({'name': name, 'value':a['max_delivery'][time_step]})

	name = 'demand_%s' % a['name']
	fg['constants'].append({'name': name, 'value':a['initial_demand']})

	in_water = set()
	out_water = set()
	transfer_prices = set()
	joint_transfer_prices = set()
	variables = []
	for p in wg['pipelines']:
		pname = 'w_%s_%s' % (p['from'], p['to'])

		if a['name'] in (p['from'], p['to']):
			variables.append(pname)

		if a['name'] == p['to']:
			in_water.add(pname)

		if a['name'] == p['from']:
			out_water.add(pname)
			tpname = 'tp_%s_%s' % (p['from'], p['to'])
			joint_transfer_prices.add("%s*%s" % (pname, tpname))
			transfer_prices.add(tpname)

	fname = '%s_money' % a['name']
	fg['functions'].append({'name': fname, 'variables': variables})

	# generating money functions structure
	func.write("\n\t\t\n\tdef %s(self, values):\n" % (fname))
	for v in variables:
		func.write("\t\t%s = values[\"%s\"]\n" % (v, v))

	func.write("\t\t\n")

	for tp in transfer_prices:
		func.write("\t\t%s = self.fg.constants[\"%s\"]\n" % (tp, tp))

	func.write("\t\tprice = self.fg.constants[\"price\"]\n")

	func.write("\t\t\n")
	if len(in_water) > 0:
		func.write("\t\tin_water = %s\n" % (' + '.join(in_water)))
	else:
		func.write("\t\tin_water = 0\n")
	if len(out_water) > 0:
		func.write("\t\tout_water = %s\n" % (' + '.join(out_water)))
	else:
		func.write("\t\tout_water = 0\n")
	func.write("\t\tvalue = (out_water - in_water) * price - (%s)\n" % (' + '.join(joint_transfer_prices)))

	func.write("\t\t\n")
	func.write("\t\treturn value * -1")





	fname = '%s_supply' % a['name']
	fg['functions'].append({'name': fname, 'variables': variables})

	# generating supply functions structure
	func.write("\n\t\t\n\tdef %s(self, values):\n" % (fname))
	for v in variables:
		func.write("\t\t%s = values[\"%s\"]\n" % (v, v))

	func.write("\t\t\n")
	if len(in_water) > 0:
		func.write("\t\tin_water = %s\n" % (' + '.join(in_water)))
	else:
		func.write("\t\tin_water = 0\n")
	if len(out_water) > 0:
		func.write("\t\tout_water = %s\n" % (' + '.join(out_water)))
	else:
		func.write("\t\tout_water = 0\n")

	func.write("\t\t\n")
	func.write("\t\tmax_delivery_%s = self.fg.constants[\"max_delivery_%s\"]\n" % (a['name'], a['name']))
	func.write("\t\tdemand_%s = self.fg.constants[\"demand_%s\"]\n" % (a['name'], a['name']))
	func.write("\t\t\n")
	md_name = 'max_delivery_%s' % a['name']
	func.write("\t\tvalue = abs(demand_%s - in_water + out_water - %s)\n" % (a['name'], md_name))
	func.write("\t\t\n")
	func.write("\t\treturn value")




fgf = open('fg.json', 'w')
fgf.write(json.dumps(fg, indent=4))
fgf.close()
func.close()
import sys, os, argparse, datetime, contextlib, subprocess, tempfile


class UserError(Exception):
	def __init__(self, message, *args):
		super().__init__(message.format(*args))


def log(message, *args):
	print('{}: {}'.format(sys.argv[0], message.format(*args)))


def command(*args, cwd = None):
	process = subprocess.Popen(args, cwd = cwd)
	process.wait()
	
	if process.returncode:
		raise UserError('Command failed: {}'.format(' '.join(args)))


def size(value):
	parts = value.split(':')
	
	if len(parts) != 2:
		raise ValueError('Size specification must contain exactly one color.')
	
	width, height = parts
	
	return float(width), float(height)


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('start_year', type = int, nargs = '?')
	parser.add_argument('start_week', type = int, nargs = '?')
	parser.add_argument('--weeks-per-page', type = int, default = 10)
	parser.add_argument('--pages', type = int, default = 1)
	parser.add_argument('--cell-size', type = size, default = size('39:18'))
	parser.add_argument('--paper-size', type = size, default = size('297:210'))
	
	args = parser.parse_args()
	
	if args.start_week is None:
		if args.start_year is not None:
			parser.error('Either none or both a start year and week need to be specified.')
		
		args.start_year, args.start_week, _ = datetime.date.today().isocalendar()
	
	return args


def datetime_from_iso_week(year, week):
	ret = datetime.datetime.strptime('{:04}-{:02}-1'.format(year, week), '%Y-%W-%w')
	
	if datetime.date(year, 1, 4).isoweekday() > 4:
		ret -= datetime.timedelta(days = 7)
	
	return ret


@contextlib.contextmanager
def temporary_directory(debug = False):
	if debug:
		yield tempfile.mkdtemp(dir = '.')
	else:
		with tempfile.TemporaryDirectory() as temp_dir:
			yield temp_dir


month_names = 'Januar Februar März April Mäi Juni Juli Auguscht Septämber Oktober Novämber Dezämber'.split()


def main(start_year, start_week, weeks_per_page, pages, cell_size, paper_size):
	for page in range(pages):
		first_week = datetime_from_iso_week(start_year, start_week) + datetime.timedelta(weeks = page * weeks_per_page)
		first_week_year, first_week_day, _ = first_week.isocalendar()
		out_path = '{:04}-W{:02}.pdf'.format(first_week_year, first_week_day)
		
		with temporary_directory() as temp_dir:
			asy_path = os.path.join(temp_dir, 'a.asy')
			pdf_path = os.path.join(temp_dir, 'a.pdf')
			
			with open(asy_path, 'w', encoding = 'utf-8') as file:
				def write(line, *args):
					print(line.format(*args), file = file)
				
				def label(font, size, alignment, text, position_expression, *args):
					write('label("{{\\setmainfont{{{}}} {}}}", {}, {}, fontsize({}pt));', font, text, position_expression.format(*args), alignment, size)
				
				write('texpreamble("\\usepackage{{fontspec}}");')
				write('int weeks_per_page = {};', weeks_per_page)
				write('pair paper_size = ({}mm, {}mm);', *paper_size)
				write('pair cell_size = ({}mm, {}mm);', *cell_size)
				write('pen cell_border_pen = {}pt + black;', 1)
				write('real header_width = {}mm;', 5)
				write('pair raster(real x, real y) {{ return (paper_size - (cell_size.x * 7 - header_width, cell_size.y * weeks_per_page)) / 2 + (cell_size.x * x, cell_size.y * y); }}')
				
				for i in range(1, weeks_per_page):
					write('draw(raster(0, {0}) -- raster(7, {0}), cell_border_pen);', i)
				
				for i in range(1, 7):
					write('draw(raster({0}, 0) -- raster({0}, weeks_per_page), cell_border_pen);', i)
				
				for i in range(weeks_per_page):
					week = first_week + datetime.timedelta(weeks = i)
					_, week_number, _ = week.isocalendar()
					
					label('OfficinaSansITC-Medium', 24, 'W', '{}'.format(week_number), 'raster(0, {} + 1 / 2)', weeks_per_page - i - 1)
					
					for j in range(7):
						day = week + datetime.timedelta(j)
						month_name = month_names[day.month - 1]
						
						if i == 0 and j == 0 or day.day == 1 and day.month == 1:
							cell_label = '{}. {} {}'.format(day.day, month_name, day.year)
						elif day.day == 1:
							cell_label = '{}. {}'.format(day.day, month_name)
						else:
							cell_label = '{}'.format(day.day)
						
						label('OfficinaSansITC-Book', 12, 'SE', cell_label, 'raster({}, {})', j, weeks_per_page - i)
				
				write('draw(box(raster(0, 0), raster(7, weeks_per_page)), cell_border_pen);')
				
				write('clip(box((0, 0), paper_size));')
				write('fixedscaling((0, 0), paper_size);')
			
			command('asy', '-f', 'pdf', '-tex', 'xelatex', os.path.relpath(asy_path, temp_dir), cwd = temp_dir)
			
			os.rename(pdf_path, out_path)
			
			log('Created {}.', out_path)


try:
	main(**vars(parse_args()))
except UserError as e:
	log('error: {}', e)
	sys.exit(1)
except KeyboardInterrupt:
	log('Operation interrupted.')
	sys.exit(1)
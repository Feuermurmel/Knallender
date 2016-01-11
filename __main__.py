import sys, os, argparse, datetime, contextlib, subprocess, tempfile


class UserError(Exception):
	def __init__(self, message, *args):
		super().__init__(message.format(*args))


def log(message, *args):
	print('{}: {}'.format(sys.argv[0], message.format(*args)))


def command(*args):
	process = subprocess.Popen(args)
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


def main(start_year, start_week, weeks_per_page, pages, cell_size, paper_size):
	out_path = '{:04}-W{:02}.asy'.format(start_year, start_week)
	first_week = datetime_from_iso_week(start_year, start_week)
	
	with open(out_path, 'w', encoding = 'utf-8') as file:
		def write(line, *args):
			print(line.format(*args), file = file)
		
		write('int weeks_per_page = {};', weeks_per_page)
		write('pair paper_size = ({}mm, {}mm);', *paper_size)
		write('pair cell_size = ({}mm, {}mm);', *cell_size)
		write('pen row_header_font = font({!r}, {}mm);', 'OfficinaSansITC-Medium', 8)
		write('pen cell_font = font({!r}, {}mm);', 'OfficinaSansITC-Book', 4)
		write('pen cell_border_pen = {}pt + black;', 1)
		write('real header_width = {}mm;', 15)
		write('pair raster(real x, real y) {{ return (paper_size - (cell_size.x * 7 - header_width, cell_size.y * weeks_per_page)) / 2 + (cell_size.x * x, cell_size.y * y); }}')
		
		for i in range(1, weeks_per_page):
			write('draw(raster(0, {0}) -- raster(7, {0}), cell_border_pen);', i)
		
		for i in range(1, 7):
			write('draw(raster({0}, 0) -- raster({0}, weeks_per_page), cell_border_pen);', i)
		
		write('draw(box(raster(0, 0), raster(7, weeks_per_page)), cell_border_pen);')
		
		write('clip(box((0, 0), paper_size));')
		write('fixedscaling((0, 0), paper_size);')
	
	command('asy', '-f', 'pdf', '-tex', 'xelatex', out_path)


try:
	main(**vars(parse_args()))
except UserError as e:
	log('error: {}', e)
	sys.exit(1)
except KeyboardInterrupt:
	log('Operation interrupted.')
	sys.exit(1)
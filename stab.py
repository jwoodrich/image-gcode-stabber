from PIL import Image, ImageDraw, ImageColor
import sys

if len(sys.argv)<2:
  print("usage: {} <filename>".format(sys.argv[0]))
  sys.exit(1)

filename=sys.argv[1]

gcode_line_number=0

image = Image.open(filename)

print("The size of the Image is: ")
print(image.format, image.size, image.mode)

# parameters for cnc machine and bit in mm
HOLE_SIZE_MAX=1.73
HOLE_SIZE_MIN=0.5
TOOL_MAX_DEPTH=4.5
#TOOL_MAX_DEPTH=9.5
WORKSPACE_WIDTH=150
WORKSPACE_HEIGHT=100
WORKSPACE_ZRANGE=40
WORKSPACE_ZBASE=0
WORKSPACE_ZMOVE=6
WORKSPACE_ZMAX=30
WORKSPACE_XMIN=-75
WORKSPACE_YMIN=0
MATERIAL_THICKNESS=0.5

hole_offset=3.0
preview_scale=8

#image=image.rotate(-90, expand=True)

# resize the image to fit ... largest side should fit into workspace
resize_factor=min(WORKSPACE_WIDTH/image.size[0],WORKSPACE_HEIGHT/image.size[1])
print("will resize by ",resize_factor)
image=image.resize((int(image.size[0]*resize_factor),int(image.size[1]*resize_factor)))

preview = Image.new(mode='L', size=(int(WORKSPACE_WIDTH*hole_offset*preview_scale),int(WORKSPACE_HEIGHT*hole_offset*preview_scale)))
draw = ImageDraw.Draw(preview)

draw.rectangle(xy=(0, 0, preview.width, preview.height), fill='black')
half_offset=int(hole_offset/2)

def gcode_spindle_on(speed):
  return "M3 S"+str(speed)+"\n"

def gcode_move(x=None,y=None,z=None,rapid=True):
  #elements=["G%d"%(gcode_line_number)]
  elements=["G01" if not rapid else "G0"]
  #gcode_line_number+=5
  if x is not None:
    elements.append("X%f"%(x))
  if y is not None:
    elements.append("Y%f"%(y))
  if z is not None:
    elements.append("Z%f"%(z))
  return " ".join(elements)+"\n"

with open(filename+".gcode","w") as fp:
  fp.write(gcode_move(z=WORKSPACE_ZMAX))
  fp.write(gcode_move(x=WORKSPACE_XMIN, y=WORKSPACE_YMIN))
  fp.write(gcode_spindle_on(speed=2000))
  for y in range(0,image.height):
    # skip every other row
    if y%2==1:
      continue
    for x in range(0,image.width):
      # skip every other column
      if x%2==1:
        continue
      # optimization to alternate working left to right and right to left by row
      if y%4>0:
        x=image.width-x
      cnc_x=WORKSPACE_XMIN+x
      cnc_y=WORKSPACE_YMIN-y
      middle=((x+half_offset)*preview_scale,(y+half_offset)*preview_scale)
      pixel=image.getpixel((x,y))[0]
      #pixel=image.getpixel((x,y))
      intensity=0.5*(pixel/255)
      hole_size=HOLE_SIZE_MAX*intensity
      half_hole_size=hole_size/2
      hole_depth=0-(intensity*TOOL_MAX_DEPTH)-MATERIAL_THICKNESS
      circle_size=int(hole_size*preview_scale)
      half_circle_size=int(circle_size/2)
      print("pixel %d,%d=%s "%(x,y,pixel))

      if hole_size>0:
        draw.ellipse((middle[0]-half_circle_size,middle[1]-half_circle_size,middle[0]+half_circle_size,middle[1]+half_circle_size), fill='white', outline='white')
        fp.write(gcode_move(x=cnc_x+half_hole_size, y=cnc_y+half_hole_size))
        fp.write(gcode_move(z=WORKSPACE_ZBASE+hole_depth))
        fp.write(gcode_move(z=WORKSPACE_ZMOVE))

#preview.show()


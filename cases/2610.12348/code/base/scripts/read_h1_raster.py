"""Read visible color strokes from original embedded H1 rasters for checking only.
Axis calibration is manually read from tick centers; pixels are not author arrays.
No extracted quantity is used to generate a trajectory or fit the Hamiltonian.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
base=Path('outputs/checks/source-inspection-continuation')
colors={'GS':[128,0,128],'state1':[255,0,0],'state2':[0,170,0],
        'state3':[255,128,0],'state4':[0,0,255],'state5':[153,102,51]}
panels=[
 dict(statistics='fermion',image='H1-source-panel-0.png',x0=117.4,xunits_per_pixel=20/84.1,
      y0=307.0,yunits_per_pixel=100/70.4,xmax=611,names=['GS','X50K0','X50K2','X66K0','X66K3','X68K4']),
 dict(statistics='boson',image='H1-source-panel-1.png',x0=132.3,xunits_per_pixel=10/76.3,
      y0=308.0,yunits_per_pixel=100/55.4,xmax=617,names=['GS','X22K0','X22K1','X38K0','X38K6','X40K14'])
]
times=[0,1,2,3,5,8,10,15,20,30,40,50,60,75,100]
for p in panels:
    file=base/p['image'];a=np.asarray(Image.open(file).convert('RGB'),dtype=int)
    p['image_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();p['curves']=[]
    for (key,col),name in zip(colors.items(),p['names']):
        mask=np.max(abs(a-np.array(col)),axis=2)<=10;points=[]
        for t in times:
            x=int(round(p['x0']+t/p['xunits_per_pixel']))
            if x>p['xmax']:continue
            yy,xx=np.nonzero(mask[6:305,max(0,x-1):x+2]);yy=yy+6
            if len(yy)<2:continue
            yl,yh=int(yy.min()),int(yy.max())
            # Deliberately bounded pixel intervals, including line width/calibration allowance.
            points.append(dict(time=t,
                time_interval=[max(0,t-2*p['xunits_per_pixel']),t+2*p['xunits_per_pixel']],
                value=(p['y0']-float(np.median(yy)))*p['yunits_per_pixel'],
                value_interval=[(p['y0']-yh-2)*p['yunits_per_pixel'],(p['y0']-yl+2)*p['yunits_per_pixel']],
                pixel_column=x,pixel_y_interval=[yl,yh]))
        p['curves'].append(dict(id=name,color=col,points=points))
out=base/'h1-raster-readings.json'
out.write_text(json.dumps(dict(panels=panels,limits=[
 'Diagnostic figure readings, not author raw data, confidence intervals, or scientific acceptance tolerances.',
 'Calibration from displayed tick centers; conservative 2-pixel allowance and visible line width.',
 'Missing/overlapping/clipped lines are omitted, not imputed. Early steep curves have horizontal uncertainty.',
 'Values are for comparisons only; independent dynamics inputs contain no source image or reading.'
]),indent=2)+'\n')
print(json.dumps({'readings':sum(len(c['points']) for p in panels for c in p['curves']),'output':str(out)}))

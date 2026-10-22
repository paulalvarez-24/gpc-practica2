# gpc-practica2

# Práctica 2 – Actividad 1: Transformaciones afines

Programa de Gráficos por Computadora (CETYS Universidad) que carga un modelo 3D en formato .obj y le aplica traslación, rotación y escalamiento en los ejes X, Y y Z con sliders.

Equipo Amarillo: Abel Martinez, Omar Munoz y Paul Alvarez. Esta actividad la hizo Paul.

## Archivos

- `practica2_act1.py`: el programa.
- `suzanne.obj`: modelo de prueba (la cabeza de mono de Blender).

## Requisitos

Python 3 y estas librerías:

```
pip install pygame PyOpenGL numpy pygame-widgets
```

## Cómo correrlo

1. Descarga los dos archivos y ponlos en la misma carpeta.
2. Ejecuta el programa:

```
python practica2_act1.py
```

## Cómo usarlo

- Hay tres columnas de sliders, una por transformación, con un slider por eje (X, Y, Z):
  - Traslación: de −5 a 5
  - Rotación: de −180° a 180°
  - Escalamiento: de 0.1 a 2
- Con la tecla **L** se abre un selector de archivos para cargar otro modelo .obj.
- Para cerrar el programa, cierra la ventana.

## Notas

- Si la traslación en Z llega cerca de 5, el modelo desaparece porque pasa por donde está la cámara. No es un error.
- En el código, la variable `USAR_MATRICES` cambia entre hacer las transformaciones con matrices (NumPy) o con las funciones de OpenGL (`glTranslatef`, `glRotatef`, `glScalef`).
- El selector de archivos se abre en un proceso aparte porque en Mac tkinter choca con pygame.

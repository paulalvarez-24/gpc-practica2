import os
import math
import numpy as np
import pygame
import pygame_widgets
import subprocess
import sys
from pygame_widgets.slider import Slider
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

USAR_MATRICES = True


#Leer el archivo .obj y regresa los vértices y las caras en triángulos
def cargar_obj(ruta):
    vertices = []
    caras = []
    with open(ruta) as archivo:
        for linea in archivo:
            partes = linea.split()
            if len(partes) == 0:
                continue
            if partes[0] == "v":
                vertices.append([float(partes[1]), float(partes[2]), float(partes[3])])
            elif partes[0] == "f":
                # "1/2/3" nos quedamos con el 1 y le restamos 1
                indices = [int(p.split("/")[0]) - 1 for p in partes[1:]]
                # partir la cara en triángulos
                for i in range(1, len(indices) - 1):
                    caras.append((indices[0], indices[i], indices[i + 1]))
    return np.array(vertices), caras


#centra el modelo en el origen y lo escala para que quepa entre -1 y 1
def normalizar(vertices):
    centro = (vertices.max(axis=0) + vertices.min(axis=0)) / 2
    vertices = vertices - centro
    return vertices / np.abs(vertices).max()

##bre el selector de archivos en un proceso aparte (Mac)
#y regresa la ruta elegida
def elegir_archivo():
    codigo = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "ventana = tk.Tk()\n"
        "ventana.withdraw()\n"
        "ventana.attributes('-topmost', True)\n"
        "print(filedialog.askopenfilename(title='Elige un modelo .obj', "
        "filetypes=[('Modelo OBJ', '*.obj')]))\n"
        "ventana.destroy()\n"
    )
    resultado = subprocess.run([sys.executable, "-c", codigo],
                               capture_output=True, text=True)
    if resultado.returncode != 0:
        print("No se pudo abrir el selector:", resultado.stderr)
    return resultado.stdout.strip()


#Dibuja el modelo triángulo por triángulo
def Modelo(lista_vertices, caras, colores):
    glBegin(GL_TRIANGLES)
    for cara in caras:
        for v in cara:
            glColor3fv(colores[v])
            glVertex3fv(lista_vertices[v])
    glEnd()


#on las funciones de OpenGL, primero escalar, luego rotar y al final trasladar
def Transformar_opengl(tx, ty, tz, rx, ry, rz, sx, sy, sz):
    glTranslatef(tx, ty, tz)
    glRotatef(rz, 0, 0, 1)
    glRotatef(ry, 0, 1, 0)
    glRotatef(rx, 1, 0, 0)
    glScalef(sx, sy, sz)


#con multiplicación de matrices
def Transformar_matriz(vertices, tx, ty, tz, rx, ry, rz, sx, sy, sz):
    ax = math.radians(rx)
    ay = math.radians(ry)
    az = math.radians(rz)

    cx, sex = math.cos(ax), math.sin(ax)
    cy, sey = math.cos(ay), math.sin(ay)
    cz, sez = math.cos(az), math.sin(az)

    #traslación
    T = np.array([[1, 0, 0, tx],
                  [0, 1, 0, ty],
                  [0, 0, 1, tz],
                  [0, 0, 0, 1]])

    #rotación
    Rx = np.array([[1, 0, 0, 0],
                   [0, cx, -sex, 0],
                   [0, sex, cx, 0],
                   [0, 0, 0, 1]])

    Ry = np.array([[cy, 0, sey, 0],
                   [0, 1, 0, 0],
                   [-sey, 0, cy, 0],
                   [0, 0, 0, 1]])

    Rz = np.array([[cz, -sez, 0, 0],
                   [sez, cz, 0, 0],
                   [0, 0, 1, 0],
                   [0, 0, 0, 1]])

    #escalamiento
    S = np.array([[sx, 0, 0, 0],
                  [0, sy, 0, 0],
                  [0, 0, sz, 0],
                  [0, 0, 0, 1]])

    # Se aplica de derecha a izquierda
    M = T @ Rz @ Ry @ Rx @ S

    #Agregar la columna de 1s (x, y, z, 1) y multiplicar todos los vértices de golpe
    unos = np.ones((len(vertices), 1))
    puntos = np.hstack([vertices, unos])
    nuevos = (M @ puntos.T).T
    return nuevos[:, :3]   #x, y, z


#sliders
def dibujar_botones(win, textura):
    ancho, alto = win.get_size()
    datos = pygame.image.tostring(win, "RGBA", True)
    glBindTexture(GL_TEXTURE_2D, textura)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ancho, alto, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, datos)

    # Vista 2D temporal
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, ancho, 0, alto, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    #cuadro del tamaño de la ventana con la textura de la interfaz
    glColor4f(1, 1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(0, 0)
    glTexCoord2f(1, 0)
    glVertex2f(ancho, 0)
    glTexCoord2f(1, 1)
    glVertex2f(ancho, alto)
    glTexCoord2f(0, 1)
    glVertex2f(0, alto)
    glEnd()

    #regresar
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


# columna de 3 sliders (X, Y, Z)
def crear_columna(win, x, minimo, maximo, paso, inicial):
    columna = {}
    for i, eje in enumerate(["X", "Y", "Z"]):
        columna[eje] = Slider(
            win, x, 50 + i * 45, 190, 12,
            min=minimo, max=maximo, step=paso,
            initial=inicial[i],
            colour=(200, 200, 200),
            handleColour=(0, 150, 200)
        )
    return columna


#título de la columna y el valor actual de cada slider
def dibujar_textos(win, fuente, x, titulo, columna):
    win.blit(fuente.render(titulo, True, (255, 255, 255)), (x, 5))
    for i, eje in enumerate(["X", "Y", "Z"]):
        texto = eje + " = " + str(round(columna[eje].getValue(), 1))
        win.blit(fuente.render(texto, True, (255, 255, 255)), (x, 28 + i * 45))


def main():
    pygame.init()
    display = (900, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Práctica 2 - Actividad 1: Transformaciones afines")
    glEnable(GL_DEPTH_TEST)

    gluPerspective(45, (display[0] / display[1]), 0.1, 45.0)
    glTranslatef(0.0, 0.0, -5)

    # Buscar el .obj en la misma carpeta que este archivo .py
    carpeta = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(carpeta, "suzanne.obj")

    vertices, caras = cargar_obj(ruta)
    vertices = normalizar(vertices)
    colores = (vertices + 1) / 2   # color según la posición de cada vértice

    #superficie aparte para los sliders
    win = pygame.Surface(display, pygame.SRCALPHA)
    textura = glGenTextures(1)
    fuente = pygame.font.SysFont("arial", 18)

    #Tres columnas de sliders: (x de la columna, mínimo, máximo, paso, valores iniciales)
    col_trasl = crear_columna(win, 10, -5, 5, 0.1, [0, 0, 0])
    col_rot = crear_columna(win, 230, -180, 180, 1, [0, 0, 0])
    col_escala = crear_columna(win, 450, 0.1, 2, 0.1, [1, 1, 1])

    while True:
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                ruta_nueva = elegir_archivo()
                if ruta_nueva != "":
                    try:
                        v_nuevos, c_nuevas = cargar_obj(ruta_nueva)
                        if len(v_nuevos) == 0 or len(c_nuevas) == 0:
                            print("El archivo no tiene vértices o caras")
                        else:
                            vertices = normalizar(v_nuevos)
                            caras = c_nuevas
                            colores = (vertices + 1) / 2
                            print("Cargado:", ruta_nueva)
                            print("Vértices:", len(vertices), "Triángulos:", len(caras))
                    except Exception as error:
                        print("No se pudo cargar el archivo:", error)

        # Leer el valor actual de cada slider
        tx, ty, tz = col_trasl["X"].getValue(), col_trasl["Y"].getValue(), col_trasl["Z"].getValue()
        rx, ry, rz = col_rot["X"].getValue(), col_rot["Y"].getValue(), col_rot["Z"].getValue()
        sx, sy, sz = col_escala["X"].getValue(), col_escala["Y"].getValue(), col_escala["Z"].getValue()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Dibujar el modelo (push/pop para que las transformaciones no se acumulen)
        glPushMatrix()
        if USAR_MATRICES:
            nuevos = Transformar_matriz(vertices, tx, ty, tz, rx, ry, rz, sx, sy, sz)
            Modelo(nuevos, caras, colores)
        else:
            Transformar_opengl(tx, ty, tz, rx, ry, rz, sx, sy, sz)
            Modelo(vertices, caras, colores)
        glPopMatrix()

        # sliders
        win.fill((0, 0, 0, 0))
        pygame_widgets.update(eventos)
        dibujar_textos(win, fuente, 10, "Traslación", col_trasl)
        dibujar_textos(win, fuente, 230, "Rotación (°)", col_rot)
        dibujar_textos(win, fuente, 450, "Escalamiento", col_escala)
        win.blit(fuente.render("Presiona L para cargar otro .obj", True, (255, 255, 255)), (10, 570))
        dibujar_botones(win, textura)

        pygame.display.flip()
        pygame.time.wait(10)


if __name__ == "__main__":
    main()
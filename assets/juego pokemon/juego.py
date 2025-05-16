import time

import pygame
import sys




# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
ANCHO = 800
ALTO = 600
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Pokemon: El Bosque Infinito")



# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
GRIS = (200, 200, 200)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AMARILLO = (255, 255, 0)

# Cargar fuentes
fuente_grande = pygame.font.SysFont("Arial", 48)
fuente_media = pygame.font.SysFont("Arial", 36)
fuente_pequeña = pygame.font.SysFont("Arial", 24)


# Clase para manejar mapas y transiciones
class GestorMapas:
    def __init__(self):
        self.mapas = {
            "exterior": self._cargar_mapa("mapa.png", (1500, 1080)),
            "casa1": self._cargar_mapa("casa1_interior.png", (800, 600)),  # Tamaño ajustado a la pantalla
            "casa2": self._cargar_mapa("casa2_interior.png", (800, 600)),  # Tamaño ajustado a la pantalla
            "casa3": self._cargar_mapa("casa3_interior.png", (800, 600)),  # Tamaño ajustado a la pantalla
            "casa4": self._cargar_mapa("casa4_interior.png", (800, 600)),  # Tamaño ajustado a la pantalla
        }

        # Definir puntos de entrada y salida
        # Formato: (x, y, dirección_inicial)
        self.puntos_transicion = {
            # Puertas exteriores (posición donde aparece al salir)
            "casa1_exterior": (300, 345, "abajo"),  # Delante de casa 1
            "casa2_exterior": (970, 345, "abajo"),  # Delante de casa 2
            "casa3_exterior": (370, 625, "abajo"),  # Delante de casa 3
            "casa4_exterior": (880, 700, "abajo"),  # Delante de casa 4

            # Alfombras en interiores (posición donde aparece al entrar)
            "casa1_interior": (400, 500, "arriba"),  # Centro abajo para casas
            "casa2_interior": (400, 500, "arriba"),
            "casa3_interior": (400, 500, "arriba"),
            "casa4_interior": (400, 500, "arriba"),
        }

        # Definir zonas interactivas para entrar/salir
        # Formato: (x, y, ancho, alto, destino)
        self.zonas_interactivas = {
            "exterior": [
                # Puertas de las casas
                (320, 305, 55, 40, "casa1"),  # Puerta casa 1
                (955, 305, 55, 40, "casa2"),  # Puerta casa 2
                (355, 625, 55, 40, "casa3"),  # Puerta casa 3
                (850, 660, 55, 40, "casa4"),  # Puerta casa 4
            ],
            "casa1": [(385, 550, 30, 10, "exterior")],  # Alfombra casa 1 (centrada)
            "casa2": [(385, 550, 30, 10, "exterior")],  # Alfombra casa 2
            "casa3": [(385, 550, 30, 10, "exterior")],  # Alfombra casa 3
            "casa4": [(385, 550, 30, 10, "exterior")],  # Alfombra casa 4
        }

    def _cargar_mapa(self, ruta, tamaño_predeterminado):
        """Carga un mapa desde una imagen o crea uno predeterminado si no existe"""
        try:
            mapa = pygame.image.load(ruta)
            return pygame.transform.scale(mapa, tamaño_predeterminado)
        except pygame.error:
            print(f"No se pudo cargar el mapa {ruta}. Creando uno predeterminado.")
            mapa = pygame.Surface(tamaño_predeterminado)

            # Si es el mapa exterior
            if "mapa.png" in ruta:
                mapa.fill((100, 200, 100))  # Verde para el exterior
                # Dibujar cuadrícula
                for x in range(0, tamaño_predeterminado[0], 100):
                    pygame.draw.line(mapa, NEGRO, (x, 0), (x, tamaño_predeterminado[1]))
                for y in range(0, tamaño_predeterminado[1], 100):
                    pygame.draw.line(mapa, NEGRO, (0, y), (tamaño_predeterminado[0], y))
            else:
                # Para interiores
                mapa.fill((180, 140, 100))  # Color madera
                # Dibujar alfombra en la parte inferior
                pygame.draw.rect(mapa, (150, 50, 50), (385, 550, 30, 10))  # Alfombra centrada
                # Dibujar algunos muebles (solo visual, sin colisiones)
                pygame.draw.rect(mapa, (100, 80, 60), (200, 200, 100, 60))  # Mesa
                pygame.draw.rect(mapa, (80, 60, 40), (500, 200, 80, 120))  # Armario

            return mapa

    def obtener_mapa(self, nombre_mapa):
        """Devuelve el mapa solicitado"""
        return self.mapas.get(nombre_mapa)

    def obtener_punto_transicion(self, destino_key):
        """Devuelve el punto donde debe aparecer el jugador al cambiar de mapa"""
        return self.puntos_transicion.get(destino_key)

    def comprobar_interaccion(self, jugador_rect, mapa_actual):
        """Comprueba si el jugador está interactuando con alguna zona"""
        zonas = self.zonas_interactivas.get(mapa_actual, [])
        for x, y, ancho, alto, destino in zonas:
            zona_rect = pygame.Rect(x, y, ancho, alto)
            if jugador_rect.colliderect(zona_rect):
                return destino
        return None

    def dibujar_zonas_debug(self, superficie, mapa_actual, camara_x, camara_y):
        """Dibuja las zonas interactivas en modo depuración"""
        zonas = self.zonas_interactivas.get(mapa_actual, [])
        for x, y, ancho, alto, _ in zonas:
            # Ajustar posición relativa a la cámara
            zona_rect = pygame.Rect(
                x - camara_x,
                y - camara_y,
                ancho,
                alto
            )
            pygame.draw.rect(superficie, (0, 255, 255, 180), zona_rect, 2)


# Clase para manejar colisiones
class GestorColisiones:
    def __init__(self):
        self.obstaculos = {}  # Diccionario de obstáculos por mapa
        self.debug_mode = False  # Activar para ver los hitboxes

        # Inicializar diccionarios para cada mapa
        for mapa in ["exterior", "casa1", "casa2", "casa3", "casa4"]:
            self.obstaculos[mapa] = []

        # Configurar colisiones del mapa exterior
        self._configurar_mapa_exterior()

        # No configuramos colisiones para interiores (eliminadas)

    def _configurar_mapa_exterior(self):
        """Configura las colisiones para el mapa exterior"""
        # Definir colisiones para las piedras (borde del mapa)
        tamano_piedra = 40

        # Función para agregar un segmento de piedras
        def agregar_segmento_piedras(inicio_x, inicio_y, cantidad, direccion):
            if direccion == "horizontal":
                for i in range(cantidad):
                    self.agregar_obstaculo("exterior", pygame.Rect(
                        inicio_x + i * tamano_piedra, inicio_y, tamano_piedra, tamano_piedra))
            elif direccion == "vertical":
                for i in range(cantidad):
                    self.agregar_obstaculo("exterior", pygame.Rect(
                        inicio_x, inicio_y + i * tamano_piedra, tamano_piedra, tamano_piedra))

        # Definir las piedras de manera más personalizable
        # Borde superior
        agregar_segmento_piedras(0, 0, 17, "horizontal")  # Lado izquierdo
        agregar_segmento_piedras(22 * tamano_piedra, 0, 16, "horizontal")  # Lado derecho

        # Borde inferior
        agregar_segmento_piedras(0, 1015, 6, "horizontal")  # Lado izquierdo
        agregar_segmento_piedras(15 * tamano_piedra, 1015, 22, "horizontal")  # Lado derecho

        # Borde izquierdo
        agregar_segmento_piedras(40, tamano_piedra, 26, "vertical")

        # Borde derecho
        agregar_segmento_piedras(1400 - tamano_piedra, tamano_piedra, 26, "vertical")

        # Definir colisiones para las casas
        self.agregar_casa("exterior", 240, 140, 255, 205, 85, 55, 40)  # Casa 1 (arriba izquierda)
        self.agregar_casa("exterior", 880, 140, 255, 205, 75, 55, 40)  # Casa 2 (arriba derecha)
        self.agregar_casa("exterior", 270, 485, 255, 180, 100, 55, 40)  # Casa 3 (abajo izquierda)
        self.agregar_casa("exterior", 715, 440, 370, 260, 130, 55, 40)  # Casa 4 (centro, más grande)

    def agregar_obstaculo(self, mapa, rect):
        """Agrega un obstáculo al mapa especificado"""
        self.obstaculos[mapa].append(rect)

    def agregar_casa(self, mapa, x, y, ancho, alto, puerta_x, puerta_ancho, puerta_alto=None):
        """
        Agrega una casa con una puerta en una posición específica
        x, y: coordenadas de la esquina superior izquierda de la casa
        ancho, alto: dimensiones de la casa
        puerta_x: posición x relativa a la casa donde comienza la puerta
        puerta_ancho: ancho de la puerta
        puerta_alto: alto de la puerta (si es None, se considera que ocupa toda la altura)
        """
        if puerta_alto is None:
            puerta_alto = alto  # Si no se especifica, la puerta ocupa toda la altura

        # Parte izquierda de la casa (antes de la puerta)
        if puerta_x > 0:
            self.obstaculos[mapa].append(pygame.Rect(x, y, puerta_x, alto))

        # Parte derecha de la casa (después de la puerta)
        parte_derecha_ancho = ancho - (puerta_x + puerta_ancho)
        if parte_derecha_ancho > 0:
            self.obstaculos[mapa].append(pygame.Rect(x + puerta_x + puerta_ancho, y,
                                                     parte_derecha_ancho, alto))

        # Parte superior de la casa (encima de la puerta)
        self.obstaculos[mapa].append(pygame.Rect(x + puerta_x, y, puerta_ancho, alto - puerta_alto))

    def hay_colision(self, jugador_rect, mapa_actual):
        """Comprueba si hay colisión con algún obstáculo en el mapa actual"""
        for obstaculo in self.obstaculos.get(mapa_actual, []):
            if jugador_rect.colliderect(obstaculo):
                return True
        return False

    def dibujar_debug(self, superficie, mapa_actual, camara_x, camara_y):
        """Dibuja los hitboxes de los obstáculos para depuración"""
        if not self.debug_mode:
            return

        for obstaculo in self.obstaculos.get(mapa_actual, []):
            # Ajustar la posición relativa a la cámara
            rect_camara = pygame.Rect(
                obstaculo.x - camara_x,
                obstaculo.y - camara_y,
                obstaculo.width,
                obstaculo.height
            )
            # Solo dibujar si está en pantalla
            if (rect_camara.right >= 0 and rect_camara.bottom >= 0 and
                    rect_camara.left <= ANCHO and rect_camara.top <= ALTO):
                pygame.draw.rect(superficie, (255, 0, 0, 128), rect_camara, 2)


# Clase para botones
class Boton:
    def __init__(self, x, y, ancho, alto, texto, color_normal, color_hover):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.hover = False

    def dibujar(self, superficie):
        color = self.color_hover if self.hover else self.color_normal
        pygame.draw.rect(superficie, color, self.rect, border_radius=10)
        pygame.draw.rect(superficie, NEGRO, self.rect, 3, border_radius=10)

        texto_surface = fuente_media.render(self.texto, True, NEGRO)
        texto_rect = texto_surface.get_rect(center=self.rect.center)
        superficie.blit(texto_surface, texto_rect)

    def actualizar(self, pos_mouse):
        self.hover = self.rect.collidepoint(pos_mouse)

    def esta_clickeado(self, pos_mouse, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1 and self.rect.collidepoint(pos_mouse):
                return True
        return False


# Función para la pantalla de inicio
def pantalla_inicio():
    # Crear botones
    boton_jugar = Boton(ANCHO // 2 - 100, ALTO // 2 - 100, 200, 60, "Jugar", VERDE, (100, 255, 100))
    boton_creditos = Boton(ANCHO // 2 - 100, ALTO // 2, 200, 60, "Créditos", AZUL, (100, 100, 255))
    boton_salir = Boton(ANCHO // 2 - 100, ALTO // 2 + 100, 200, 60, "Salir", ROJO, (255, 100, 100))

    titulo = fuente_grande.render("Pokemon: El Bosque Infinito", True, AMARILLO)
    titulo_rect = titulo.get_rect(center=(ANCHO // 2, ALTO // 4))

    while True:
        pos_mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if boton_jugar.esta_clickeado(pos_mouse, evento):
                return "jugar"

            if boton_creditos.esta_clickeado(pos_mouse, evento):
                return "creditos"

            if boton_salir.esta_clickeado(pos_mouse, evento):
                pygame.quit()
                sys.exit()

        # Actualizar estado de botones
        boton_jugar.actualizar(pos_mouse)
        boton_creditos.actualizar(pos_mouse)
        boton_salir.actualizar(pos_mouse)

        # Dibujar pantalla
        pantalla.fill((50, 50, 50))  # Fondo oscuro
        pantalla.blit(titulo, titulo_rect)
        boton_jugar.dibujar(pantalla)
        boton_creditos.dibujar(pantalla)
        boton_salir.dibujar(pantalla)

        pygame.display.flip()

class NPC:
    def __init__(self, imagen_path, x, y, dialogo):
        try:
            self.imagen = pygame.image.load(imagen_path)
            self.imagen = pygame.transform.scale(self.imagen, (60, 60))
        except:
            self.imagen = pygame.Surface((60, 60))
            self.imagen.fill(AZUL)

        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 40, 40)
        self.dialogo = dialogo

    def dibujar(self, superficie, camara_x, camara_y):
        superficie.blit(self.imagen, (self.x - camara_x, self.y - camara_y))

    def esta_cerca(self, jugador_rect):
        return self.rect.colliderect(jugador_rect)


# Función para la pantalla de juego
def pantalla_juego():
    gestor_mapas = GestorMapas()
    colisiones = GestorColisiones()
    mapa_actual = "exterior"

    try:
        personaje_arriba = pygame.image.load("personaje_arriba.png")
        personaje_abajo = pygame.image.load("personaje_abajo.png")
        personaje_izquierda = pygame.image.load("personaje_izquierda.png")
        personaje_derecha = pygame.image.load("personaje_derecha.png")
        personaje_tamaño = (80, 80)
        personaje_arriba = pygame.transform.scale(personaje_arriba, personaje_tamaño)
        personaje_abajo = pygame.transform.scale(personaje_abajo, personaje_tamaño)
        personaje_izquierda = pygame.transform.scale(personaje_izquierda, personaje_tamaño)
        personaje_derecha = pygame.transform.scale(personaje_derecha, personaje_tamaño)
        personaje = personaje_abajo
        direccion_actual = "abajo"
    except pygame.error:
        personaje = pygame.Surface((40, 40))
        personaje.fill(ROJO)
        direccion_actual = "abajo"

    personaje_mapa_x, personaje_mapa_y = 370, 625
    npc1 = NPC("personaje_derecha.png", 240, 1010, "¡Hola! ¿Has visto a Pikachu por aquí?")
    npc_inicial = NPC("npc_profesor.png", 400, 300, "¿Cuál Pokémon inicial quieres? (1: Planta, 2: Fuego, 3: Agua)")
    npc_inicial_interactuado = False
    mostrando_dialogo_npc = False
    texto_dialogo_actual = ""
    opcion_elegida = None

    velocidad = 5
    clock = pygame.time.Clock()
    debug_mode = False
    mensaje_interaccion = None
    tiempo_mensaje = 0
    puede_interactuar = False
    zona_interactiva = None

    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return
                elif evento.key == pygame.K_F3:
                    debug_mode = not debug_mode
                    colisiones.debug_mode = debug_mode
                elif evento.key == pygame.K_e and puede_interactuar:
                    if zona_interactiva:
                        nuevo_mapa = zona_interactiva
                        if mapa_actual == "exterior":
                            punto_clave = f"{nuevo_mapa}_interior"
                        else:
                            punto_clave = f"{mapa_actual}_exterior"

                        punto = gestor_mapas.obtener_punto_transicion(punto_clave)
                        if punto:
                            personaje_mapa_x, personaje_mapa_y, direccion_nueva = punto
                            if direccion_nueva == "arriba":
                                personaje = personaje_arriba
                            elif direccion_nueva == "abajo":
                                personaje = personaje_abajo
                            elif direccion_nueva == "izquierda":
                                personaje = personaje_izquierda
                            elif direccion_nueva == "derecha":
                                personaje = personaje_derecha
                            direccion_actual = direccion_nueva
                            mapa_actual = nuevo_mapa
                            mensaje_interaccion = "Has cambiado de mapa"
                            tiempo_mensaje = pygame.time.get_ticks()
                    elif mapa_actual == "casa4" and not npc_inicial_interactuado and npc_inicial.esta_cerca(jugador_rect):
                        mostrando_dialogo_npc = True
                        texto_dialogo_actual = "¿Cuál Pokémon inicial quieres? (1: Planta, 2: Fuego, 3: Agua)"

            elif evento.type == pygame.USEREVENT + 1:
                texto_dialogo_actual = "Me voy a explorar el Bosque Infinito."
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                npc_inicial_interactuado = True
                mostrando_dialogo_npc = False

            elif mostrando_dialogo_npc:
                if evento.type == pygame.KEYDOWN:
                    if opcion_elegida is None:
                        if evento.key == pygame.K_1:
                            texto_dialogo_actual = "¡Elegiste Planta!"
                            opcion_elegida = "Planta"
                            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
                        elif evento.key == pygame.K_2:
                            texto_dialogo_actual = "¡Elegiste Fuego!"
                            opcion_elegida = "Fuego"
                            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
                        elif evento.key == pygame.K_3:
                            texto_dialogo_actual = "¡Elegiste Agua!"
                            opcion_elegida = "Agua"
                            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)

        posicion_anterior_x = personaje_mapa_x
        posicion_anterior_y = personaje_mapa_y
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            personaje_mapa_x -= velocidad
            personaje = personaje_izquierda
            direccion_actual = "izquierda"
        if teclas[pygame.K_RIGHT]:
            personaje_mapa_x += velocidad
            personaje = personaje_derecha
            direccion_actual = "derecha"
        if teclas[pygame.K_UP]:
            personaje_mapa_y -= velocidad
            personaje = personaje_arriba
            direccion_actual = "arriba"
        if teclas[pygame.K_DOWN]:
            personaje_mapa_y += velocidad
            personaje = personaje_abajo
            direccion_actual = "abajo"

        max_x, max_y = (1500, 1080) if mapa_actual == "exterior" else (800, 600)
        personaje_mapa_x = max(0, min(personaje_mapa_x, max_x - 40))
        personaje_mapa_y = max(0, min(personaje_mapa_y, max_y - 40))

        jugador_rect = pygame.Rect(personaje_mapa_x, personaje_mapa_y, 40, 40)
        if colisiones.hay_colision(jugador_rect, mapa_actual):
            personaje_mapa_x = posicion_anterior_x
            personaje_mapa_y = posicion_anterior_y
            jugador_rect.x = personaje_mapa_x
            jugador_rect.y = personaje_mapa_y

        zona_interactiva = gestor_mapas.comprobar_interaccion(jugador_rect, mapa_actual)
        puede_interactuar = (
            zona_interactiva is not None or
            (mapa_actual == "casa4" and not npc_inicial_interactuado and npc_inicial.esta_cerca(jugador_rect))
        )

        if puede_interactuar and not mensaje_interaccion:
            mensaje_interaccion = "Presiona E para interactuar"
            tiempo_mensaje = pygame.time.get_ticks()

        if mensaje_interaccion and pygame.time.get_ticks() - tiempo_mensaje > 250:
            mensaje_interaccion = None

        if mapa_actual == "exterior":
            camara_x = max(0, min(personaje_mapa_x - ANCHO // 2, 1500 - ANCHO))
            camara_y = max(0, min(personaje_mapa_y - ALTO // 2, 1080 - ALTO))
        else:
            camara_x, camara_y = 0, 0

        pantalla.fill(NEGRO)
        mapa_superficie = gestor_mapas.obtener_mapa(mapa_actual)
        if mapa_superficie:
            pantalla.blit(mapa_superficie, (0, 0), (camara_x, camara_y, ANCHO, ALTO))

        pantalla.blit(personaje, (personaje_mapa_x - camara_x, personaje_mapa_y - camara_y))

        if mapa_actual == "casa4" and not npc_inicial_interactuado:
            npc_inicial.dibujar(pantalla, camara_x, camara_y)

        if debug_mode:
            colisiones.dibujar_debug(pantalla, mapa_actual, camara_x, camara_y)
            gestor_mapas.dibujar_zonas_debug(pantalla, mapa_actual, camara_x, camara_y)

        if mensaje_interaccion:
            mensaje_surface = fuente_media.render(mensaje_interaccion, True, AMARILLO)
            mensaje_rect = mensaje_surface.get_rect(center=(ANCHO // 2, ALTO - 50))
            pantalla.blit(mensaje_surface, mensaje_rect)

        if texto_dialogo_actual:
            dialogo_surface = fuente_pequeña.render(texto_dialogo_actual, True, BLANCO)
            dialogo_rect = dialogo_surface.get_rect(center=(ANCHO // 2, ALTO - 100))
            pygame.draw.rect(pantalla, NEGRO, dialogo_rect.inflate(20, 10))
            pantalla.blit(dialogo_surface, dialogo_rect)

        pygame.display.flip()
        clock.tick(60)

def pantalla_creditos():
    creditos = [
        ("Programación:", "Kevin"),
        ("Personajes:", "Eric"),
        ("Música:", "Pokemon"),
        ("Mapa:", "Kevin"),
        ("Personaje:", "Eric")
    ]

    y_pos = ALTO // 4

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                return  # Cualquier tecla o clic para volver

        # Dibujar pantalla
        pantalla.fill((30, 30, 30))

        # Título
        titulo = fuente_grande.render("CRÉDITOS", True, AMARILLO)
        titulo_rect = titulo.get_rect(center=(ANCHO // 2, ALTO // 8))
        pantalla.blit(titulo, titulo_rect)

        # Créditos
        for i, (rol, nombre) in enumerate(creditos):
            texto_rol = fuente_media.render(rol, True, BLANCO)
            texto_nombre = fuente_media.render(nombre, True, VERDE)

            pantalla.blit(texto_rol, (ANCHO // 4, y_pos + i * 60))
            pantalla.blit(texto_nombre, (ANCHO // 4 + 250, y_pos + i * 60))

        # Instrucción para volver
        volver = fuente_pequeña.render("Presiona cualquier tecla para volver", True, GRIS)
        volver_rect = volver.get_rect(center=(ANCHO // 2, ALTO - 50))
        pantalla.blit(volver, volver_rect)

        pygame.display.flip()


def mostrar_logo():
    run = True
    while run:
        logo = pygame.image.load("fondo_principio.png").convert()
        pantalla.blit(logo, (0, 0))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                run = False

# Bucle principal del juego
def main():
    mostrar_logo()
    while True:
        accion = pantalla_inicio()

        if accion == "jugar":
            pantalla_juego()
        elif accion == "creditos":
            pantalla_creditos()


if __name__ == "__main__":
    main()
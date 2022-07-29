# Importacion de modulos - ESP32
from machine import Pin, UART, SoftI2C, RTC # Importamos el módulo machine
import network, urequests
import utime, time # Importamos el módulo de tiempo
from Lib.sh1106 import SH1106_I2C  # Importamos el módulo de funcionamiento de la OLED
import framebuf # Módulo para visualizar imagenes en pbm

# Conexion de pines del display Oled- ESP32.
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000) # Inicializando el método I2C para ESP32
oled = SH1106_I2C(128, 64, i2c)


# Variable de activacion modulo GPS
gpsModule = UART(2, baudrate=9600)
print(gpsModule)

buff = bytearray(255)

TIMEOUT = False
FIX_STATUS = False

latitude = ""
longitude = ""
satellites = ""

# Importa logo de Geosystem_Security
def buscar_icono(ruta):
    dibujo = open(ruta, "rb")  # Abrir en modo lectura de bits
    dibujo.readline() # Metodo para ubicarse en la primera linea de los bist
    z = dibujo.readline() # Ubicarnos en la segunda linea
    x = int(z.split()[0]) # Devuelve una lista de los elementos de la variable solo 2 elemetos
    y = int(z.split()[1])
    icono = bytearray(dibujo.read()) # Guardar en matriz de bites
    dibujo.close()
    return framebuf.FrameBuffer(icono, x, y, framebuf.MONO_HLSB) # Utilizamos el metodo MONO_HLSB

oled.blit(buscar_icono("Img/Geosystem.pbm"), 0, 0) # Ruta y sitio de ubicación del directorio
oled.show()  # Mostrar en la oled
time.sleep(3) # Espera de 3 segundos
oled.fill(0)
oled.show()

# Obtener datos del modulo de GPS
def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, GPStime
    
    timeout = time.time() + 8
    
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parte = buff.split(',')
        print(parte[0], len(parte))
        oled.fill(0)
        oled.text(parte[0], 0, 10)
        oled.text("Buscando ", 0, 20)
        oled.text("Satelites... ", 0, 30)
        oled.show()
        if (parte[0] == "b'$GNGGA" and len(parte) == 15):
            if(parte[1] and parte[2] and parte[3] and parte[4] and parte[5] and parte[6] and parte[7]):
                print(buff)
                
                latitude = convertToDegree(parte[2])
                if (parte[3] == 'S'):
                    latitude = str(-float(latitude))
                longitude = convertToDegree(parte[4])
                if (parte[5] == 'W'):
                    longitude = str(-float(longitude))
                satellites = parte[7]
                GPStime = parte[1][0:2] + ":" + parte[1][2:4] + ":" + parte[1][4:6]
                FIX_STATUS = True
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        utime.sleep_ms(500)
        
def convertToDegree(RawDegrees):

    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)
      
while True:
    
    getGPS(gpsModule)
    code = 1
    
    if(TIMEOUT == True):
        print("GPS No se pudo conectar al satelite.")
        TIMEOUT = False
    
    if(FIX_STATUS == True):
        # Conexion de red WIFI
        code = 0
        if (code == 0):
            print(latitude)
            print(longitude)
            def conectaWifi (red, password):
                global miRed
                miRed = network.WLAN(network.STA_IF)     
                if not miRed.isconnected(): # Si no está conectado…
                    miRed.active(True) # Activa la interface
                    miRed.connect(red, password) # Intenta conectar con la red
                    print('Conectando a la red', red +"…")
                    timeout = time.time ()
                    while not miRed.isconnected():# Mientras no se conecte..
                        if (time.ticks_diff (time.time (), timeout) > 10):
                            return False
                    return True
            
            if conectaWifi ("Velandia", "Bogota2021*"):
                
                print ("Conexión exitosa!")
                print('Datos de la red (IP/netmask/gw/DNS):', miRed.ifconfig())
                
            # Obtener hora
            (year, month, day, weekday, hour, minute, second, milisecond) = RTC().datetime()                
            RTC().init((year, month, day, weekday, hour, minute, second, milisecond))
            Fecha = ("{:02d}/{:02d}/{}".format(RTC().datetime()[2], RTC().datetime()[1], RTC().datetime()[0])) 
            Hora = ("{:02d}:{:02d}:{:02d}".format(RTC().datetime()[4], RTC().datetime()[5], RTC().datetime()[6]))
            
            print("----------------------")
            print("Impresión de datos GPS...")
            print(" ")
            print("Ubicacion del paquete")
            print("Latitude: "+latitude)
            print("Longitude: "+longitude)
            print("Satellites: " +satellites)
            print(" ")
            print("Geosystem Security")
            print("----------------------")
        
            # Impresion de datos de geolocalizacion en Display Oled 
            oled.fill(0)
            oled.text("Ubicacion", 0, 0)
            oled.text("Lat:"+latitude, 0, 10)
            oled.text("Lng:"+longitude, 0, 20)
            oled.text("Satelite:"+satellites, 0, 30)
            oled.text("Geosystem", 0, 40)
            oled.text("Security", 0, 50)
            oled.show()
                
            FIX_STATUS = False
        
            # Envio de datos a la API    
            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng="  
            while (True):
                time.sleep(2)
                # Optener datos de la API de Google Maps en json
                respuesta = urequests.get(url+str(latitude)+","+str(longitude)+"&key=AIzaSyCI_DS7bJLWjcpDLKKK5fbIk0cuLj0hoE8")
                data = respuesta.json()
                # Formateo de resultados del json
                direccion = str(data["results"][0]["formatted_address"])
                def normalize(s):
                    replacements = (
                        (" ","_"),
                        ("#",""),
                        ("á", "a"),
                        ("é", "e"),
                        ("í", "i"),
                        ("ó", "o"),
                        ("ú", "u"),
                        ("Á", "A"),
                        ("É", "E"),
                        ("Í", "I"),
                        ("Ó", "O"),
                        ("Ú", "U"),
                        ("ñ", "n"),
                        ("Ñ", "N"),
                    )
                    for a, b in replacements:
                        s = s.replace(a, b).replace(a.upper(), b.upper())
                    return s
                direccionA=normalize(direccion)
                print(direccionA)
                print("")
                # Envio de datos a IFTTT Excel
                urlExel = "https://maker.ifttt.com/trigger/Localizacion/with/key/dgcdmmnZ_vq28EAn9BzHP3?"
                respuesta = urequests.get(urlExel+"&value1="+ str(direccionA) +"&value2="+ str(latitude)+"&value2="+ str(longitude))
                respuesta.close ()
                # Envio de datos a IFTTT Telegram
                urlTelegram = "https://maker.ifttt.com/trigger/Telegram/with/key/dgcdmmnZ_vq28EAn9BzHP3?" 
                respuesta2 = urequests.get(urlTelegram+"&value1="+ str(direccionA) +"&value2="+ str(latitude)+"&value3="+ str(longitude))
                respuesta2.close ()
                break
            else:
                print ("Imposible conectar")
                miRed.active (False)

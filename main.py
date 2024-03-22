## LIBRERIAS
import msal
from msal import PublicClientApplication
import webbrowser
import requests
## SERVER
from flask import Flask, request
from flask_cors import CORS


##########################
######## server ##########
##########################

### DEFINIMOS EL SERVIDOR
app = Flask(__name__)
CORS(app)

#########################
######## APP ############
#########################

## DATA AZURE APLICATION
APPLICATION_ID = 'f8effa76-7b57-43d7-9654-6a5d850d1236'
CLIENT_SECRET = '82l8Q~LY1tbpYklQoV.Y4rHnwH8VfE3uU_hmOcCl' ## DURA 2 AÑOS DESDE EL 26/12/2023
authority_url ="https://login.microsoftonline.com/organizations/" # COSTUMERS : 'https://login.microsoftonline.com/consumers/'
### PERMISOS QUE REQUIERE LA APP
SCOPES = ['Files.Read','Files.Read.All','Files.ReadWrite','Files.ReadWrite.All','Sites.Read.All','Sites.ReadWrite.All','User.Read','User.ReadBasic.All','User.ReadWrite']

#################################
########## GRAPH AZURE ##########
#################################

### base url
graph_url = 'https://graph.microsoft.com/v1.0/'

### ENDPOINTS ###
userInfo = 'me'
carpets = 'me/drive/root/children'
createCarpet = 'me/drive/root/children'



####################################
########## GLOBAL CLASS ############
####################################


class OneDriveControl():
        
        def __init__(self):
            self.access_token = None
        
        ##################################
        ## VERIFICACIÓN DE CREDENCIALES ##
        ##################################
            
        def startDrive(self):
            ### iniciamos sesión
            url = self.loginDrive_method_1()
            return url

        def loginDrive_method_1(self):
            ## Method 1: authorization with authorization code
            ## GENERAMOS EL CLIENTE PARA MANEJAR LA CONEXIÓN CON ONE DRIVE
            self.client_instance = msal.ConfidentialClientApplication(
                client_id=APPLICATION_ID,
                client_credential = CLIENT_SECRET,
                authority = authority_url
            )
            ## OBTENEMOS LOS PERMISOS DEL USUARIO NECESARIOS PARA EL USO DE LA APLICACIÓN
            authorization_request_url = self.client_instance.get_authorization_request_url(SCOPES)
            return authorization_request_url
            ##webbrowser.open(authorization_request_url,new=False) ## ABRIMOS PARA OBTENER EL ACCESS TOKEN
            ## redirigimos a un endpoint diferente
        def completeLogin(self,code):
            self.code  = code ## OBTENEMOS EL CODIGO DE AUTHORIZATION
            self.access_token = self.client_instance.acquire_token_by_authorization_code(
                code = code,
                scopes = SCOPES
            )
            try:
                print("ACCESS TOKEN: ",self.access_token['access_token'])
                return self.access_token['access_token']
            except Exception as e:
                return 'error al hacer la consulta'
            
        
        def userData(self,token):
            ### VERIFICAMOS SI YA NOS LOGUEAMOS
            ## LLAMAMOS AL ENDPOINT
            headers = {'Authorization':'Bearer '+token}
            ## construimos el endpoint
            endpoint = graph_url+userInfo
            ## generamos la petición
            response = requests.get(endpoint,headers=headers)
            self.userInfo = response.json()
            return self.userInfo
        
        def getCarpets(self):
            if (self.access_token == None):
                return {'status':'No te haz logueado'}
            else:
                ## LLAMAMOS AL ENDPOINT
                headers = {'Authorization':'Bearer '+self.access_token['access_token']}
                ## construimos el endpoint
                endpoint = graph_url+carpets
                response = requests.get(endpoint,headers=headers)
                self.carpets = response.json()['value']
                print("CANTIDAD CARPETAS: ",len(self.carpets))
                return self.carpets
            

        def createCarpet(self,name):
            if (self.access_token == None):
                return {'status':'No te haz logueado'}
            else:
                ### preparamos el endpoint
                ## LLAMAMOS AL ENDPOINT
                headers = {'Authorization':'Bearer '+self.access_token['access_token']}
                ## construimos el endpoint
                endpoint = graph_url+createCarpet
                body = {
                    'name':name,
                    'folder':{
                        
                    }
                }

                response = requests.post(endpoint,json=body,headers=headers)
                response.json()
                return response.json()
            

        def verifyFolders(self):
            carpets = self.getCarpets()
            if (self.access_token != None):
                ### esto quiere decir que me traje las carpetas
                ### verificamos si existen las 3 carpetas (informe_brilla,informe_potenciales,informe_construcciones,imagenes_inferencia,retroalimentacion_construcciones,retroalimentacion_potenciales,retroalimentación_brilla)
                ## definimos la lista:
                find_carpets = ['informe_brilla','informe_potenciales','informe_construcciones','imagenes_inferencia','retroalimentacion_construcciones','retroalimentacion_potenciales','retroalimentación_brilla']
                target_carpets = []

                for target in find_carpets:
                    ### filtramos las carpetas
                    lista_filtrada = [obj for obj in carpets if obj['name'] == target]
                    if(len(lista_filtrada) == 0):
                        ## CREAMOS LA CARPETA
                        data_carpet = self.createCarpet(target)
                        print("CARPETA CREADA: ",data_carpet)
                        target_carpets.append(data_carpet)
                    else:
                        ## agregamos su información en la lista
                        target_carpets.append(lista_filtrada[0])

                    ## DEVUELVO LA INFORMACIÓN DE LAS CARPETAS
                ### CREAMOS UN ARCHIVO EN LA PRIMERA CARPETA DE PRUEBAS
                
                return target_carpets
            else:
                return carpets
        ### FUNCIÓN PARA CREAR ARCHIVO EN UN CARPETA ESPECIFICA
            
        def createFileInCarpet(self,name_carpet,name,content):
            ### VERIFICAMOS SI TENEMOS EL TOKEN
            if (self.access_token == None):
                return {'status':'No te haz logueado'}
            else:
                ## LLAMAMOS AL ENDPOINT
                headers = {'Authorization':'Bearer '+self.access_token['access_token']}
                ## construimos el endpoint
                endpoint = graph_url+'me/drive/root:/{}/{}:/content'.format(name_carpet,name)
                ## leemos el contenido del archivo
                
                ## hacemos la petición
                response = requests.put(endpoint,data=content,headers=headers)
                
                return response

        def getFilesInCarpet(self,nameCarpet):
            ### VERIFICAMOS SI TENEMOS EL TOKEN
            if (self.access_token == None):
                return {'status':'No te haz logueado'}
            else:
                ### DEFINIMOS LA PETICIÓN
                headers = {'Authorization':'Bearer '+self.access_token['access_token']}
                ## construimos el endpoint
                endpoint = graph_url+'me/drive/root:/{}:/children'.format(nameCarpet)
                response = requests.get(endpoint,headers=headers)
                return response.json()['value']
####################################
########### CLASS INSTANCE #########
####################################

drive_control = OneDriveControl()

###################################
########## BACKEND FUNCTIONS ######
###################################

@app.route('/Login', methods=['GET'])
def login():
    url = drive_control.startDrive()
    return {'link':url}

@app.route('/Authorization_code', methods=['POST'])
def Authorization_code():
    ### OBTENEMOS LOS PARAMETROS DE LA URL
    data = request.json
    code = data["code"]

    if (code == None):
        return {'status':'No fue autorizado el inicio de sesión.'}
    else:
        access_token = drive_control.completeLogin(code)
        return {'token':access_token}


@app.route('/getuserData', methods=['POST'])
def getUserData():
    data = request.json
    token = data["token"]
    data_user = drive_control.userData(token)
    return data_user
    

@app.route('/getCarpets',methods=['GET'])

def getUserCarpets():
    
    data  = drive_control.getCarpets()
    return data

@app.route('/verifyFolders',methods=['GET'])

def verifyFolders():
    data = drive_control.verifyFolders()

    return data
    #data = drive_control.createCarpet(data['name'])

@app.route('/createFile',methods=['POST'])
def createFileCarpet():
    ## obtenemos los datos
    file = request.files['file']
    name = request.form.get('name')
    carpet_name =  request.form.get('carpet_name')
    ## guardamos en la carpeta en especifica
    response = drive_control.createFileInCarpet(carpet_name,name,file)
    return response

## TRAERNOS LOS ARCHIVOS DE UNA CARPETA ESPECIFICA
@app.route('/getFiles',methods=['GET'])

def getFileCarpet():
    ### obtenemos el nombre de la carpeta
    data = request.json
    nameCarpet = data['name']
    response = drive_control.getFilesInCarpet(nameCarpet=nameCarpet)
    return response

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
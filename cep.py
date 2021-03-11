import json 
import requests
import re
import sys
import pandas as pd
import os

class CEP:
    def __init__(self, 
                url_base_api_viacep = "http://www.viacep.com.br/ws",
                db_local_address    = "data/Banco_ceps.xlsx"):

        self.url_base_api_viacep = url_base_api_viacep
        self.db_local = self.__get_data_in_local_db__(db_local_address)

    def __get_data_in_local_db__(self, db_local_address):
        """consulta dados do banco de dados local e armazena em lista

        Returns:
            list: lista de ceps com informacoes ((localidade, cep_inicial, cep_final))
        """
        if (os.path.exists(db_local_address)):
            # Lendo banco de dados de acordo com extensao
            if db_local_address[-4::] == ".csv":
                db_ceps_local = pd.read_csv(f"{db_local_address}")
            elif db_local_address[-5::] == ".xlsx":
                db_ceps_local = pd.read_excel(f"{db_local_address}")

            # Extraindo e armazenando (localidade, cep_inicial, cep_final) do banco de ceps local
            list_db_local = []
            for index, row in db_ceps_local.iterrows():
                list_db_local.append((row['Localidade'], row['CEP Inicial'], row['CEP Final']))  

            return list_db_local
        else:
            print(f"Banco de dados local '{db_local_address}', nao existe")
            exit()

        return None


    def __valida_cep_expreg__(self, cep):
        """valida cep através de máscaras, antes de verificacao em bancos de dados.

        Args:
            cep (str): cep para consulta

        Returns:
            bool: retorna True se cep corresponde à uma das mascaras
        """
        # lista de expressoes permitidas
        list_patterns = (r"^\d{2}.\d{3}-\d{3}$", r"^\d{8}$")
        for pattern in list_patterns:
            if(re.match(pattern, cep)):
                return True
                
        return False
    

    def __get_list_of_ceps_fetched__(self, ceps_address="data/ceps.csv"):
        """le arquivo com lista de CEPs a serem buscados.
           
        Args:
            ceps_address (str, optional): Contém o endereco do arquivo com a lista de ceps. Defaults to "ceps.csv".

        Returns:
            list: lista de ceps

        Obs:
            Cada linha do arquivo deve conter um endereco de CEP.
        """
        list_of_ceps_fetched = []
        if(os.path.exists(ceps_address)): # Verificando existencia do arquivo          
            with open(f"{ceps_address}","r") as file_ceps_address:
                for line_cep in file_ceps_address:
                    line_cep = line_cep.strip() # removendo '\n'
                    if(self.__valida_cep_expreg__(line_cep)):
                        # limpando string 'line_cep' (Removendo '.' e '-')
                        line_cep = line_cep.replace(".",""); line_cep = line_cep.replace("-","")
                        list_of_ceps_fetched.append(str(line_cep))
        else:
            print(f"Arquivo {ceps_address} não existe!")
            exit()

        return list_of_ceps_fetched


    def __get_api_viacep__(self, cep_end):
        """executa um get na API VIACEP

        Args:
            cep_end (str): endereço do cep a ser consultado

        Returns:
            dict: retorna dict com informações do cep, ou informação de erro
        """
        response = requests.get(f"{self.url_base_api_viacep}/{cep_end}/json/")
        if response:
            return response.json()
        else:
            return response
            

    def __get_cities__(self, ceps_address="data/ceps.csv"):
        """realiza busca

        Args:
            ceps_address (str, optional): endereco de arquivo que contem lista de CEPs. Defaults to 'data/ceps.csv'.

        Returns:
            list: lista de cidades encontradas
        Obs:
            Cada linha do arquivo deve conter um endereco de CEP.
        """
        list_cities_found = []        
        # Le arquivo e Armazena CEPs a serem consultados
        list_of_ceps_fetched = self.__get_list_of_ceps_fetched__(ceps_address)

        # Se TRUE, autoriza verificação dos ceps
        if len(list_of_ceps_fetched) > 0:
            
            # Inicia busca                
            for i in range(len(list_of_ceps_fetched)):
                str_cep_searched = list_of_ceps_fetched[i]

                # 1º - Verifica em cada item do banco de dados local
                cep_existent_local_db = False
                for (localidade, cep_inicial, cep_final) in self.db_local:                        
                    if(int(str_cep_searched) >= int(cep_inicial) and int(str_cep_searched) <= int(cep_final)):
                        list_cities_found.append(localidade) # Encontrou na base Local
                        cep_existent_local_db = True
                        break

                # 2º - Se cep não foi encontrado em banco de dados local, buscar em API
                if cep_existent_local_db != True:
                    info_cep = self.__get_api_viacep__(str_cep_searched)  # Buscando em API
                    
                    if('erro' not in info_cep.keys()):                        
                        list_cities_found.append((info_cep['localidade'])) # Encontrou na API
                    else:
                        list_cities_found.append((f"CEP {str_cep_searched} não encontrado"))

        else:
            print("Lista de CEPs vazio!")

        return list_cities_found


    def __write_output_csv__(self, filename_out="output", header="HEADER", list_cities_found=None):
        """escreve dados em formato de saida CSV

        Args:
            filename_out (str, optional): nome para o arquivo de saida. Defaults to "output".
            header (str, optional): valor do header do arquivo de saida. Defaults to "HEADER".
            list_cities_found (list, optional): lista de valores a serem escritos. Defaults to None.
        """
        cities = pd.DataFrame(list_cities_found)
        cities.to_csv(f"{filename_out}.csv", index=False, header=[header])
                  
        print(f"    Saida gravado em arquivo '{filename_out}.csv'")


# Tests
if __name__ == "__main__":

    command_line = """Ajuda - Linha de comando
        1º argumento corresponde ao caminho do banco de dados local de ceps (.csv ou .xlsx)
        2º argum. corresponde ao caminho do arquivo que contém os CEPs que serão consultados
        
        ex: python3 cep.py data/Banco_ceps.xlsx data/ceps.csv
    """ 
    print(command_line)

    print("Start ..")
    # Argumentos de entrada
    db_local = sys.argv[1]  
    file_ceps = sys.argv[2]
    
    cep = CEP(db_local_address=db_local)

    # Consultando CEPs
    list_cities_found = cep.__get_cities__(ceps_address=file_ceps)

    if(len(list_cities_found) > 0):
        # Escrevendo saida em formato CSV
        cep.__write_output_csv__(filename_out="output_cities", header="Localidade", list_cities_found=list_cities_found)
         
    print("Finished!")
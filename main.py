from cep import CEP

if __name__ == "__main__":

    print("Start ..")

    cep = CEP()
    
    # Consultando CEPs
    list_cities_found = cep.__get_cities__()

    if(len(list_cities_found) > 0):
        # Escrevendo saida em formato CSV
        cep.__write_output_csv__(header="Localidade", list_cities_found=list_cities_found, filename_out="output_cities")
         
    print("Finished!")
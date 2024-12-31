from selenium import webdriver
from selenium.webdriver.common.by import By
import env

# Inicializando o navegador
driver = webdriver.Chrome()
driver.get('https://x.com/?mx=2')

# Aguardar o carregamento da página (opcional)
driver.implicitly_wait(10)  # Espera até 10 segundos para carregar os elementos

# Verificar se a div que contém o elemento com texto "Entrar" existe
try:
    span_entrar = driver.find_element(By.XPATH, "//span[text()='Entrar']")
    span_entrar.click()

    driver.implicitly_wait(10)
    input_email = driver.find_element(By.XPATH, "//input[@autocomplete='username']")
    input_email.send_keys(env.user_email)

    driver.implicitly_wait(10)
    span_next = driver.find_element(By.XPATH, "//span[text()='Avançar']")
    span_next.click()

    driver.implicitly_wait(10)
    input_password = driver.find_element(By.XPATH, "//input[@autocomplete='current-password']")
    input_email.send_keys(env.user_password)

    driver.implicitly_wait(10)
    span_next = driver.find_element(By.XPATH, "")
    span_next.click()

except Exception as e:
    # Caso a div não seja encontrada, exibe a mensagem
    print("Div com 'Entrar' não encontrada.", e)

# Aguarda a interação até que você pressione Enter
input("Pressione Enter para fechar o navegador...")

driver.quit()

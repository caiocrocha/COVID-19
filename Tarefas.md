# 15 Abril de 2020
## Estudar o artigo original do PDBBind
Escrever um resumo sobre a importância de ter um banco de dados curado para a avaliação das campanhas de Virtual Screening, Docking etc.   
Descrever como é realizada a curadoria dos dados.

## Implementar o bounding shape no DockFlow.py.
Bounding shape é uma rotina para calcular as dimensões de uma molécula de um arquivo .mol2.
Ele calcula as coordenadas cartesianas de máximo e mínimo e o centro geométrico.

* Incluir os argumentos --ref --padding no DockFlow.py
    * Ref indica um ligante de referencia para definir o centro do sitio de ligacao e as dimensoes.
      Atualmente ele usa a flag --ligand e armazena em "ref_ligand".
    * Padding é uma distancia extra em cada dimensão
      Essa distância extra pode ser usada por novos ligantes para assim ocuparem novos sítios de ligação na proteína.

* Fazer o redock para todas as instancias do PDBBind
  * Calcular o RMSD entre as poses dos resultados e a estrutura do cristal ( ligand.mol2 )
  * Calcular a taxa de sucesso (poses boas, médias e ruins)

# 03 de junho
## Para sexta feira
### Redock e rescore do casp3
* Desenhar a curva ROC
* Calcular energia do cristal com diferentes funções de pontuação
### Redock e rescore do pdbbind-2019
* Curva ROC
## Estudar artigos
* Performance da triagem
* Aprendizagem de máquina para criar funções específicas para cada dataset
* Apresentar um desses artigos para a próxima sexta feira (12)

# 12 de junho
* Repetir o CASF-2016, no modo RESCORE Usando: DLSCORE e DeltaVinaXGB, Smina e Vinardo.
* Apresentar sobre o artigo do CASF-2016 para 26 de junho
## PDBbind: correlação de Pearson com e sem outliers

# 17 jun
* Otimizacao local do CASF-2016

# Para o futuro
Avaliar o impacto do tamanho da caixa de busca no sucesso etc do docking.

# Para o futuro 2
As tarefas são:
1. Baixar o arquivo com as atividades
2. Baixar as estruturas dos compostos
3. Baixar 1 das estruturas da Main Protease no PDB
4. Realizar do docking de todos os compostos, usando o Vina gerando 10 poses
5. Calcular o scoring power
6. Calcular o ranking power
7. Calcular o ER para 1%, 5% e 10%.
8. Calcular a curva ROC e a AUC.

# 15 de julho
## Diego
* Refazer docking da renina
## Caio
* Indicar no relatorio do PDBbind sobre resultados incorretos e rescore+local_opt
* Incluir nova curva ROC da caspase no relatorio
* Fazer relatorio da SARS-CoV-1
* EF para o CASF-2016
### Para a próxima quarta-feira, 29/07/2020.
* Rever o artigo do CASF-2016.
* Mostrar rapidamente o que ja foi discutido na apresentação anteiror.
* Apresentar agora a segunda parte do artigo, onde os autores exploram as diferenças entre os pockets das proteínas, que eles dividiram em 3 descritores com 3 subcategorias cada.
### Para o futuro
* Fazer graficos do CASF-2016
    * Box plot modificado
    * Horizontal stacked bar

import pulp
import gurobipy as gp 
from gurobipy import GRB 

# Definir conjuntos y parámetros
ZT = range(1, 31)  # Periodos de tiempo
S = range(1, 11)   # Secciones o checkpoints
P = range(1, 11)   # Posiciones de comparsa
G = range(1, 11)   # Bloques del desfile

T = 3 * 3600  # Duración esperada del desfile en segundos (3 horas)
di = 90       # Longitud de la sección en metros
#B = 150    # Máximo GAP en metros
L = 3000    # Longitud recorrida del desfile en metros

# Parámetros adicionales
Tao = 500 # Longitud del periodo en segundos
Lk = {1: 114,2: 325,3: 312,4: 275,5: 316,6: 242,7: 349,8: 112,9: 148,10: 148}  # Longitud del Bloque K en metros
Vk = {1: 1.08, 2: 1.61, 3: 1.72, 4: 1.69, 5: 0.63, 6:2.48 ,7: 2.37, 8: 0.78, 9: 0.22 , 10: 2.71}  # Velocidad promedio del bloque K en m/s
# Crear una instancia del problema
prob = pulp.LpProblem("DesfileCarnaval", pulp.LpMinimize)

# Variables
X = pulp.LpVariable.dicts("X", ((i, k) for i in P for k in G), cat='Binary') #Asignación deñ bloque k en posición i
Y = pulp.LpVariable.dicts("Y", ((k, t) for k in G for t in ZT)) #Distancia recorrida bloque k en tiempo t
Lmax = pulp.LpVariable("Lmax", lowBound=0)
B = pulp.LpVariable("B", lowBound=0)
#Inicializar X con una asignación fija
asignacion_fija = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10:10}
for i in P:
    for k in G:
        if asignacion_fija[i] == k:
            X[i, k].setInitialValue(1)
            X[i, k].fixValue()
        else:
            X[i, k].setInitialValue(0)
            X[i, k].fixValue()

# Función objetivo
prob += L-Lmax
# Restricciones
for k in G:
    prob += pulp.lpSum(X[i, k] for i in P) == 1  # Cada bloque k debe salir en una posición i
for i in P:
    prob += pulp.lpSum(X[i, k] for k in G) == 1  # Cada posición i debe ser ocupada por un bloque k

for k in G:
    for t in ZT:
        prob += Y[k, t] <= Vk[k] * Tao * t  # Cota de localización

M = 3600  # Constante grande para las restricciones de gap
for t in ZT:
    if t <= (len(ZT)):  # Comprobar que t no sea el último período de tiempo
        for i in range(1, len(P)):  # Iterar sobre las posiciones
            for k1 in G:
                for k2 in G:
                    if k1 != k2:
                        prob += (Y[k1, t] - Y[k2, t] - Lk[k1] - 10) >= -M * (2 - X[i, k1] - X[i + 1, k2])  # Restricción de gap k1 adelante de k2
                        prob += (Y[k1, t] - Y[k2, t]) <= B + M * (2 - X[i, k1] - X[i + 1, k2])      # Restricción de gap k1 adelante de k2
    if t == len(ZT):
        for k in G:
            prob += Lmax <= Y[k, t]  #  de localización máxima
prob += B <= 359
solver = pulp.GUROBI_CMD(msg=1, options=[('IterationLimit', 10000)])
# Resolver el problema
prob.solve(solver)

for t in ZT:
    W=100000000
    if t == len(ZT):
        for k in G:
            W=min(W, Y[k,t].varValue)

# Imprimir el estado de la solución
print("Estado:", pulp.LpStatus[prob.status])

# Imprimir variables de decisión
for v in prob.variables():
    print(v.name, "=", v.varValue)

# Imprimir el valor de la función objetivo
print("Valor de la función objetivo:", pulp.value(prob.objective))

# Longitud máxima alcanzada por el desfile
#max_length = pulp.value(Lmax)

# Bloques asignados a las posiciones
positions = {i: None for i in P}
for i, k in X.keys():
    if pulp.value(X[i, k]) == 1:
        positions[i] = k

# Valor de la función objetivo
objective_value = pulp.value(prob.objective)

# Imprimir resumen de la solución
#print("Longitud máxima alcanzada por el desfile:", max_length)
print("Asignación de bloques a posiciones:")
for position, block in positions.items():
    print(f"Posición {position}: Bloque {block}")
print("Valor de la función objetivo:", objective_value)
# Imprimir las variables Y por cada t
for t in ZT:
    print(f"Tiempo {t}:")
    for k in G:
        print(f"Y_{k}_{t} =", Y[k, t].varValue)
print(W)
print(B.varValue)

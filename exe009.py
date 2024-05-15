n = int(input('Informe um número para a tabuada: '))
i = 1;
print('-'*12)
while i <= 10:
    print('{:2} x {:2} = {:2}'.format(n, i, n*i))
    i += 1
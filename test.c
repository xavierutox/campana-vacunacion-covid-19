#include <stdio.h>
#include "sthread.h"
 
static sthread_t tfib;
static sthread_t tlucas;

 
static void fib(int n);
static void lucas (int n);

int main(){
	int n;
	printf(“ingrese n”);
	scanf(“%d”, %n);
	sthread_create(&tfib, &fib,n)
	int rfib = sthread_join(tfib);
    sthread_create(&tlucas, &lucas,n)
	int rlucas = sthread_join(tlucas);
    int raiz = pow (5, 0.5)
    int resultado = (rlucas+rfib*raiz)/2;
    printf("Resultado=%d\n", resultado);
	



    return 0;
}

void fib(n){
    int resultado;
    if (n==0){
        resultado=0;
    }else if (n==1)
    {
        resultado=1;
    }else{
        sthread_t n1,n2;
        sthread_create(&n1, &fib, n-1);
        sthread_create(&n1, &fib, n-2);
        resultado = sthread_join(n1)+sthread_join(n2);
    }
    Sthread_exit(result);
}
void luacs(n){
    int resultado;
    if (n==0){
        resultado=2;
    }else if (n==1)
    {
        resultado=1;
    }else{
        sthread_t n1,n2;
        sthread_create(&n1, &lucas, n-1);
        sthread_create(&n1, &lucas, n-2);
        resultado = sthread_join(n1)+sthread_join(n2);
    }
    Sthread_exit(result);
}

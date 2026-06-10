import java.util.Scanner;

class Cifrador {
    public String cifrar(String mensaje) {
        String textoAlterado = "";
        for (int i = 0; i < mensaje.length(); i++) {
            char letra = mensaje.charAt(i);
            char letraCifrada = (char) (letra + i); 
            textoAlterado = textoAlterado + letraCifrada;
        }
        String textoCifradoFinal = "";
        for (int i = textoAlterado.length() - 1; i >= 0; i--) {
            textoCifradoFinal = textoCifradoFinal + textoAlterado.charAt(i);
        }
        return textoCifradoFinal;
    }
    public String descifrar(String mensajeCifrado) {
        String textoInvertido = "";
        for (int i = mensajeCifrado.length() - 1; i >= 0; i--) {
            textoInvertido = textoInvertido + mensajeCifrado.charAt(i);
        }
        String textoDescifradoFinal = "";
        for (int i = 0; i < textoInvertido.length(); i++) {
            char letra = textoInvertido.charAt(i);
            char letraDescifrada = (char) (letra - i); 
            textoDescifradoFinal = textoDescifradoFinal + letraDescifrada;
        }
        return textoDescifradoFinal;
    }
}

public class Main {
    public static void main(String[] args) {
        Scanner teclado = new Scanner(System.in);
        System.out.println("Ingresa el mensaje que deseas cifrar:");
        String mensajeOriginal = teclado.nextLine();
        Cifrador miCifrador = new Cifrador();

        String mensajeCifrado = miCifrador.cifrar(mensajeOriginal);
        String mensajeDescifrado = miCifrador.descifrar(mensajeCifrado);

        System.out.println("\n--- RESULTADOS DEL CIFRADO ---");
        System.out.println("Mensaje original: " + mensajeOriginal);
        System.out.println("Mensaje cifrado:  " + mensajeCifrado);
        System.out.println("Mensaje descifrado: " + mensajeDescifrado);
        teclado.close();
    }
}
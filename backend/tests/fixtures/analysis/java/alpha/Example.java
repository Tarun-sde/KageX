package alpha;
public class Example {
    private int value;
    public int choose(int x) {
        if (x > 0) return x;
        return value;
    }
    public static class Nested {
        public int one() { return 1; }
    }
}

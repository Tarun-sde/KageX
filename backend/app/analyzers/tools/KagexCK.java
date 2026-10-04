import com.github.mauricioaniche.ck.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.*;
import org.apache.log4j.LogManager;

/** KageX-owned wrapper. Only parses copied Java text, with no submitted jars. */
public final class KagexCK {
    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }
    public static void main(String[] args) throws Exception {
        LogManager.getRootLogger().setLevel(org.apache.log4j.Level.OFF);
        Path root = Paths.get(args[0]);
        List<Path> valid = new ArrayList<>();
        Map<String, int[]> positions = new HashMap<>();
        for (String relative : Files.readAllLines(Paths.get(args[1]))) {
            Path path = root.resolve(relative);
            String source;
            try { source = Files.readString(path, StandardCharsets.UTF_8); }
            catch (java.nio.charset.CharacterCodingException error) {
                System.out.println("W\tFILE_PARSE_FAILED\t" + encode(relative)); continue;
            }
            ASTParser parser = ASTParser.newParser(AST.JLS11);
            Map<String, String> options = JavaCore.getOptions();
            JavaCore.setComplianceOptions(JavaCore.VERSION_11, options);
            parser.setCompilerOptions(options);
            parser.setSource(source.toCharArray());
            CompilationUnit unit = (CompilationUnit) parser.createAST(null);
            if (Arrays.stream(unit.getProblems()).anyMatch(problem -> problem.isError())) {
                System.out.println("W\tFILE_PARSE_FAILED\t" + encode(relative)); continue;
            }
            valid.add(path);
            unit.accept(new ASTVisitor() {
                public void preVisit(ASTNode node) {
                    if (!(node instanceof AbstractTypeDeclaration)) return;
                    AbstractTypeDeclaration type = (AbstractTypeDeclaration) node;
                    String name = type.getName().getIdentifier();
                    for (ASTNode parent = node.getParent(); parent != null; parent = parent.getParent()) {
                        if (parent instanceof AbstractTypeDeclaration)
                            name = ((AbstractTypeDeclaration) parent).getName().getIdentifier() + "$" + name;
                    }
                    if (unit.getPackage() != null) name = unit.getPackage().getName().getFullyQualifiedName() + "." + name;
                    positions.put(relative + "::" + name, new int[] {unit.getLineNumber(node.getStartPosition()), unit.getLineNumber(node.getStartPosition() + node.getLength() - 1)});
                }
            });
        }
        List<CKClassResult> results = new ArrayList<>();
        Set<String> errors = new HashSet<>();
        new CK(false, 100, false).calculate(root, new CKNotifier() {
            public void notify(CKClassResult result) { results.add(result); }
            public void notifyError(String file, Exception error) { errors.add(file); }
        }, valid.toArray(new Path[0]));
        results.sort(Comparator.comparing(CKClassResult::getFile).thenComparing(CKClassResult::getClassName));
        for (String file : errors) System.out.println("W\tFILE_PARSE_FAILED\t" + encode(root.relativize(Paths.get(file)).toString()));
        for (CKClassResult result : results) {
            if (errors.contains(result.getFile())) continue;
            String relative = root.relativize(Paths.get(result.getFile())).toString();
            int[] location = positions.get(relative + "::" + result.getClassName());
            if (location == null) {
                System.out.println("W\tJAVA_ENTITY_LOCATION_UNAVAILABLE\t" + encode(relative)); continue;
            }
            System.out.println(String.join("\t", "E", encode(relative), encode(result.getClassName()),
                Integer.toString(location[0]), Integer.toString(location[1]),
                Integer.toString(result.getWmc()), Integer.toString(result.getDit()), Integer.toString(result.getNoc()),
                Integer.toString(result.getCbo()), Integer.toString(result.getRfc()), Integer.toString(result.getLcom()),
                Integer.toString(result.getLoc()), Integer.toString(result.getNumberOfMethods()), System.getProperty("java.version")));
        }
    }
}

package team.creditburners.repository;

import java.nio.file.*;
import java.io.IOException;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

@Repository
public class SnapshotRepository {
    private final Map<String, JsonNode> snapshots = new LinkedHashMap<>();
    private final Map<String, Path> assets = new HashMap<>();
    public SnapshotRepository(@Value("${sensei.data-dir:data/prepared-v1}") String directory,
            @Value("${sensei.snapshots-file:results/qwen3.8-27b-ctx640-probe-emptycheck-shared-alwayscompliant-full-v1/snapshots.json}") String snapshotsFile) throws IOException {
        Path root = Path.of(directory).toRealPath();
        Path assetRoot = root.resolve("assets").toRealPath();
        JsonNode data = JsonMapper.builder().build().readTree(Path.of(snapshotsFile).toFile());
        if (!data.isArray()) throw new IllegalArgumentException("snapshots.json must contain an array");
        for (JsonNode snapshot : data) {
            String id = snapshot.path("snapshot_id").asText();
            if (id.isBlank() || snapshots.putIfAbsent(id, snapshot) != null)
                throw new IllegalArgumentException("Missing or duplicate snapshot ID");
            register(snapshot.path("image_url").asText(), assetRoot);
            for (JsonNode area : snapshot.path("areas")) {
                register(area.path("crop_url").asText(), assetRoot);
                if (!area.path("reference").isNull())
                    register(area.path("reference").path("crop_url").asText(), assetRoot);
            }
        }
    }

    private void register(String url, Path root) throws IOException {
        if (!url.startsWith("/assets/")) return;
        String id = url.substring(8);
        if (!id.matches("[A-Za-z0-9_.-]+")) throw new IllegalArgumentException("Unsafe asset ID");
        Path candidate = root.resolve(id);
        if (Files.isRegularFile(candidate)) {
            Path real = candidate.toRealPath();
            if (!real.startsWith(root)) throw new IllegalArgumentException("Asset escapes published directory");
            assets.put(id, real);
        }
    }

    public Collection<JsonNode> findAll() { return snapshots.values(); }
    public JsonNode findById(String id) { return snapshots.get(id); }
    public Path findAsset(String id) { return assets.get(id); }
}

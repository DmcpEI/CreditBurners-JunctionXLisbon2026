package team.creditburners.controller;

import team.creditburners.service.SnapshotService;
import team.creditburners.dto.SnapshotSummary;
import java.nio.file.Path;
import java.util.List;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import tools.jackson.databind.JsonNode;

@RestController
public class SnapshotsController {
    private final SnapshotService service;
    public SnapshotsController(SnapshotService service) { this.service = service; }
    @GetMapping("/api/snapshots")
    public List<SnapshotSummary> list() { return service.list(); }
    @GetMapping("/api/snapshots/{id}")
    public JsonNode detail(@PathVariable String id) { return service.detail(id); }
    @GetMapping("/assets/{id}")
    public ResponseEntity<FileSystemResource> asset(@PathVariable String id) {
        Path path = service.asset(id);
        MediaType type = MediaTypeFactory.getMediaType(path.getFileName().toString())
            .orElse(MediaType.APPLICATION_OCTET_STREAM);
        return ResponseEntity.ok().contentType(type).header("X-Content-Type-Options", "nosniff")
            .body(new FileSystemResource(path));
    }
}

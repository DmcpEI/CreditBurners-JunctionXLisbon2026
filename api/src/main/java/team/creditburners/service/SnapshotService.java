package team.creditburners.service;

import team.creditburners.repository.SnapshotRepository;
import team.creditburners.dto.SnapshotSummary;
import java.nio.file.*;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.JsonNode;

@Service
public class SnapshotService {
    private final SnapshotRepository repository;
    public SnapshotService(SnapshotRepository repository) { this.repository = repository; }
    public List<SnapshotSummary> list() {
        return repository.findAll().stream().map(SnapshotSummary::from).toList();
    }
    public JsonNode detail(String id) {
        JsonNode snapshot = repository.findById(id);
        if (snapshot == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return snapshot;
    }
    public Path asset(String id) {
        Path path = repository.findAsset(id);
        if (path == null || !Files.isRegularFile(path))
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return path;
    }
}

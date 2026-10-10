package team.creditburners.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import tools.jackson.databind.JsonNode;

public record SnapshotSummary(
    @JsonProperty("snapshot_id") String snapshotId,
    @JsonProperty("camera_id") String cameraId,
    @JsonProperty("image_file") String imageFile,
    @JsonProperty("captured_at") String capturedAt,
    @JsonProperty("image_url") String imageUrl
) {
    public static SnapshotSummary from(JsonNode snapshot) {
        return new SnapshotSummary(snapshot.path("snapshot_id").asText(),
            snapshot.path("camera_id").asText(), snapshot.path("image_file").asText(),
            snapshot.path("captured_at").asText(), snapshot.path("image_url").asText());
    }
}

import { Button } from "../components/Button";
import { Placeholder } from "../components/Placeholder";

export function NotFound() {
  return (
    <Placeholder
      title="This page wandered off"
      body="We couldn't find what you were looking for. Let's head back home."
    >
      <Button to="/">Back to home →</Button>
    </Placeholder>
  );
}

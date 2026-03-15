import { Component, type ErrorInfo, type ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type Props = { children: ReactNode }
type State = { hasError: boolean; error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="font-display">Something went wrong</CardTitle>
            <CardDescription>This section encountered an error and could not render.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <pre className="max-h-32 overflow-auto rounded-lg bg-muted p-3 font-mono text-xs text-muted-foreground">
              {this.state.error?.message ?? "Unknown error"}
            </pre>
            <Button
              variant="outline"
              size="sm"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try again
            </Button>
          </CardContent>
        </Card>
      )
    }
    return this.props.children
  }
}

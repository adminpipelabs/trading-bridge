import { useGateway } from './hooks/useGateway';
import { LoginScreen } from './components/LoginScreen';
import { ChatView } from './components/ChatView';

function App() {
  const { messages, connection, isStreaming, connect, disconnect, sendMessage, abortChat } = useGateway();

  if (connection.status === 'connected') {
    return (
      <ChatView
        messages={messages}
        isStreaming={isStreaming}
        onSend={sendMessage}
        onAbort={abortChat}
        onDisconnect={disconnect}
      />
    );
  }

  return <LoginScreen onConnect={connect} connection={connection} />;
}

export default App;

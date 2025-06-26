import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Container, 
  Form, 
  Row, 
  Col, 
  Table, 
  Card, 
  Badge, 
  Alert,
  Spinner,
  Modal,
  Navbar,
  Nav,
  Dropdown
} from 'react-bootstrap';
import Select from 'react-select';
import axios from 'axios';
import FileUploader from './components/fileUploader';

const App = () => {
  const REACT_APP_BACKEND_SERVICE = process.env.REACT_APP_BACKEND_SERVICE;
  const [user, setUser] = useState(null);
  const [spreadsheets, setSpreadsheets] = useState([]);
  const [newSpreadsheetTitle, setNewSpreadsheetTitle] = useState('');
  const [selectedParticipant, setSelectedParticipant] = useState(null);
  const [isDisabled, setIsDisabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [alertMessage, setAlertMessage] = useState(null);

  // Participant options for React Select
  const participantOptions = [
    { value: 'zerodha', label: 'Zerodha', icon: '🏦' },
    { value: 'grow', label: 'Grow', icon: '📈' },
    { value: 'icici', label: 'ICICI Direct', icon: '🏛️' },
    { value: 'hdfc', label: 'HDFC Securities', icon: '🏦' },
    { value: 'kotak', label: 'Kotak Securities', icon: '🏛️' },
    { value: 'angel_one', label: 'Angel One', icon: '👼' },
    { value: 'upstox', label: 'Upstox', icon: '📊' },
    { value: 'five_paisa', label: '5paisa', icon: '💰' },
    { value: 'sharekhan', label: 'Sharekhan', icon: '🦁' },
    { value: 'motilal_oswal', label: 'Motilal Oswal', icon: '📈' },
    { value: 'edelweiss', label: 'Edelweiss', icon: '🌿' },
    { value: 'axis', label: 'Axis Securities', icon: '🏛️' },
    { value: 'sbicap', label: 'SBI Capital', icon: '🏦' },
    { value: 'india_informs', label: 'India Infoline', icon: '📰' },
    { value: 'rksv', label: 'RKSV', icon: '📊' },
    { value: 'samco', label: 'SAMCO', icon: '📈' },
    { value: 'alice_blue', label: 'Alice Blue', icon: '🔵' },
    { value: 'finvasia', label: 'Finvasia', icon: '💼' },
    { value: 'master_trust', label: 'Master Trust', icon: '🤝' },
    { value: 'iifl', label: 'IIFL Securities', icon: '🏛️' },
    { value: 'religare', label: 'Religare', icon: '🏥' },
    { value: 'karvy', label: 'Karvy', icon: '📊' },
    { value: 'geodisha', label: 'Geodisha', icon: '🌍' },
    { value: 'bonanza', label: 'Bonanza', icon: '🎰' },
    { value: 'aditya_birla', label: 'Aditya Birla Capital', icon: '🏢' },
    { value: 'jm_financial', label: 'JM Financial', icon: '💰' },
    { value: 'phillip_capital', label: 'Phillip Capital', icon: '🏛️' },
    { value: 'nirmal_bang', label: 'Nirmal Bang', icon: '📊' },
    { value: 'prabhudas_lilladher', label: 'Prabhudas Lilladher', icon: '🏛️' },
    { value: 'smc', label: 'SMC Global', icon: '🌐' },
    { value: 'yes_securities', label: 'YES Securities', icon: '✅' },
    { value: 'first_global', label: 'First Global', icon: '🌍' },
    { value: 'emkay', label: 'Emkay Global', icon: '📈' },
    { value: 'centrum', label: 'Centrum Broking', icon: '🏛️' },
    { value: 'elite', label: 'Elite Wealth', icon: '👑' },
    { value: 'lkp', label: 'LKP Securities', icon: '📊' },
    { value: 'mirae_asset', label: 'Mirae Asset', icon: '🌅' },
    { value: 'nomura', label: 'Nomura', icon: '🏛️' },
    { value: 'ubs', label: 'UBS', icon: '🏛️' },
    { value: 'credit_suisse', label: 'Credit Suisse', icon: '🏛️' },
    { value: 'goldman_sachs', label: 'Goldman Sachs', icon: '🏛️' },
    { value: 'morgan_stanley', label: 'Morgan Stanley', icon: '🏛️' },
    { value: 'citigroup', label: 'Citigroup', icon: '🏛️' },
    { value: 'bank_of_america', label: 'Bank of America', icon: '🏛️' },
    { value: 'jp_morgan', label: 'JP Morgan', icon: '🏛️' },
    { value: 'deutsche_bank', label: 'Deutsche Bank', icon: '🏛️' },
    { value: 'barclays', label: 'Barclays', icon: '🏛️' },
    { value: 'hsbc', label: 'HSBC', icon: '🏛️' },
    { value: 'standard_chartered', label: 'Standard Chartered', icon: '🏛️' },
    { value: 'rbl', label: 'RBL Bank', icon: '🏦' },
    { value: 'idfc', label: 'IDFC Securities', icon: '🏛️' },
    { value: 'equirus', label: 'Equirus Securities', icon: '🏛️' },
    { value: 'anand_rathi', label: 'Anand Rathi', icon: '🏛️' },
    { value: 'spa_securities', label: 'SPA Securities', icon: '🏛️' },
    { value: 'ventura', label: 'Ventura Securities', icon: '📈' },
    { value: 'capital_via', label: 'Capital Via', icon: '💼' },
    { value: 'tata_capital', label: 'Tata Capital', icon: '🏢' },
    { value: 'bajaj_capital', label: 'Bajaj Capital', icon: '🏢' },
    { value: 'dhanuka', label: 'Dhanuka', icon: '📊' },
    { value: 'gepl', label: 'GEPL Capital', icon: '💼' },
    { value: 'inventure', label: 'Inventure Growth', icon: '📈' },
    { value: 'krishna_capital', label: 'Krishna Capital', icon: '💰' },
    { value: 'lkp_securities', label: 'LKP Securities', icon: '📊' },
    { value: 'mangal_keshav', label: 'Mangal Keshav', icon: '🏛️' },
    { value: 'marwadi', label: 'Marwadi Shares', icon: '📊' },
    { value: 'networth', label: 'Networth Stock Broking', icon: '💰' },
    { value: 'oriental', label: 'Oriental Bank', icon: '🏦' },
    { value: 'pinc', label: 'PINC Research', icon: '🔍' },
    { value: 'prime', label: 'Prime Securities', icon: '🏛️' },
    { value: 'ratnakar', label: 'Ratnakar Bank', icon: '🏦' },
    { value: 'sbi_capital', label: 'SBI Capital', icon: '🏦' },
    { value: 'sebi_registered', label: 'SEBI Registered', icon: '📋' },
    { value: 'tamilnadu', label: 'Tamil Nadu Mercantile', icon: '🏛️' },
    { value: 'unicon', label: 'Unicon Securities', icon: '🏛️' },
    { value: 'ventura_securities', label: 'Ventura Securities', icon: '📈' },
    { value: 'way2wealth', label: 'Way2Wealth', icon: '💰' },
    { value: 'wealth_desk', label: 'Wealth Desk', icon: '💼' },
    { value: 'zerodha_broking', label: 'Zerodha Broking', icon: '🏦' }
  ];

  // Custom styles for React Select
  const customStyles = {
    control: (provided, state) => ({
      ...provided,
      borderColor: state.isFocused ? '#0d6efd' : '#dee2e6',
      boxShadow: state.isFocused ? '0 0 0 0.2rem rgba(13, 110, 253, 0.25)' : 'none',
      '&:hover': {
        borderColor: '#0d6efd'
      }
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected ? '#0d6efd' : state.isFocused ? '#e9ecef' : 'white',
      color: state.isSelected ? 'white' : '#212529',
      '&:hover': {
        backgroundColor: state.isSelected ? '#0d6efd' : '#e9ecef'
      }
    })
  };

  // Custom option component for React Select
  const CustomOption = ({ data, innerProps }) => (
    <div {...innerProps} style={{ padding: '8px 12px', cursor: 'pointer' }}>
      <span style={{ marginRight: '8px' }}>{data.icon}</span>
      {data.label}
    </div>
  );

  const fetchSpreadsheets = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/`, { withCredentials: true });
      console.log("Spreadsheets: ", res);
      setSpreadsheets(res.data);
    } catch (error) {
      console.error('Error fetching spreadsheets:', error);
      setAlertMessage({ type: 'danger', text: 'Failed to fetch spreadsheets' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const res = await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/auth/user`, { withCredentials: true });
        console.log("Response: ", res.data);
        setUser(res.data);
        fetchSpreadsheets();
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    };

    const isFormValid = newSpreadsheetTitle.length > 0 && selectedParticipant;
    setIsDisabled(!isFormValid);

    fetchUserData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newSpreadsheetTitle, selectedParticipant]);

  const handleSyncData = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`http://${REACT_APP_BACKEND_SERVICE}/data/sync`, {
        'spreadsheets': spreadsheets
      }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await res.data;
      console.log(data);
      setAlertMessage({ type: 'success', text: 'Data synced successfully!' });
    } catch (error) {
      console.error('Error syncing data:', error);
      setAlertMessage({ type: 'danger', text: 'Failed to sync data' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSpreadsheet = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/`, {
        title: newSpreadsheetTitle,
        metadata: {
          participant_name: selectedParticipant.value,
          created_at: new Date().toISOString(),
          account_type: 'demat'
        }
      }, { withCredentials: true });
      console.log('Created spreadsheet:', res.data);
      fetchSpreadsheets();
      setNewSpreadsheetTitle('');
      setSelectedParticipant(null);
      setShowCreateModal(false);
      setAlertMessage({ type: 'success', text: 'Spreadsheet created successfully!' });
    } catch (error) {
      console.error('Error creating spreadsheet:', error);
      setAlertMessage({ type: 'danger', text: 'Failed to create spreadsheet' });
    } finally {
      setLoading(false);
    }
  };

  const handleSpreadsheetLinkClick = (url) => {
    window.open(url, '_blank');
  };

  const handleDeleteClick = async (spreadsheet_url) => {
    if (window.confirm('Are you sure you want to delete this spreadsheet?')) {
      try {
        console.log("Deleting a spreadsheet with spreadsheetId:", spreadsheet_url);
        const spreadsheet_id = spreadsheet_url.split('/d/')[1]?.split('/')[0];
        if (!spreadsheet_id) {
          console.error('Invalid spreadsheet URL');
          return;
        }
        
        const res = await axios.delete(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/${spreadsheet_id}`, { 
          withCredentials: true 
        });
        console.log('Spreadsheet deleted successfully:', res.data);
        fetchSpreadsheets();
        setAlertMessage({ type: 'success', text: 'Spreadsheet deleted successfully!' });
      } catch(error) {
        console.error('Error deleting spreadsheet:', error);
        setAlertMessage({ type: 'danger', text: 'Failed to delete spreadsheet' });
      }
    }
  };
  
  const handleSignOut = async () => {
    try {
      await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/auth/logout`, { withCredentials: true });
      console.log("Clearing local storage and session storage");
      localStorage.clear();
      sessionStorage.clear();
      setUser(null);
      setSpreadsheets([]);
      window.location.reload();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const handleDebugSession = async () => {
    try {
      const res = await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/auth/debug-session`, { 
        withCredentials: true 
      });
      console.log('Debug session response:', res.data);
    } catch (error) {
      console.error('Error debugging session:', error);
    }
  };

  const getParticipantLabel = (participantValue) => {
    const participant = participantOptions.find(p => p.value === participantValue);
    return participant ? participant.label : 'Unknown';
  };

  const getParticipantIcon = (participantValue) => {
    const participant = participantOptions.find(p => p.value === participantValue);
    return participant ? participant.icon : '❓';
  };

  if (!user) {
    console.log("backend service is:", REACT_APP_BACKEND_SERVICE);
  }

  return (
    <div className="App">
      {/* Navigation Bar */}
      {user && (
        <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
          <Container>
            <Navbar.Brand>📊 Stock Portfolio Manager</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="ms-auto">
                <Dropdown>
                  <Dropdown.Toggle variant="outline-light" id="dropdown-basic">
                    👤 {user.name}
                  </Dropdown.Toggle>
                  <Dropdown.Menu>
                    <Dropdown.Item onClick={handleDebugSession}>
                      🔧 Debug Session
                    </Dropdown.Item>
                    <Dropdown.Divider />
                    <Dropdown.Item onClick={handleSignOut}>
                      🚪 Sign Out
                    </Dropdown.Item>
                  </Dropdown.Menu>
                </Dropdown>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>
      )}

      <Container>
        {/* Alert Messages */}
        {alertMessage && (
          <Alert 
            variant={alertMessage.type} 
            dismissible 
            onClose={() => setAlertMessage(null)}
            className="mb-4"
          >
            {alertMessage.text}
          </Alert>
        )}

        {user && (
          <div>
            {/* Welcome Section */}
            <Card className="mb-4">
              <Card.Body className="text-center">
                <h2>Welcome back, {user.name}! 👋</h2>
                <p className="text-muted">Manage your stock portfolio with accurate broker-specific calculations</p>
              </Card.Body>
            </Card>

            {/* Spreadsheets Table */}
            <Card className="mb-4">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0">📋 Your Spreadsheets</h5>
                <Button 
                  variant="primary" 
                  onClick={() => setShowCreateModal(true)}
                  disabled={loading}
                >
                  {loading ? <Spinner animation="border" size="sm" /> : '➕ Create New'}
                </Button>
              </Card.Header>
              <Card.Body>
                {loading ? (
                  <div className="text-center py-4">
                    <Spinner animation="border" />
                    <p className="mt-2">Loading spreadsheets...</p>
                  </div>
                ) : spreadsheets.length === 0 ? (
                  <div className="text-center py-4">
                    <p className="text-muted">No spreadsheets found. Create your first one!</p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <Table hover>
                      <thead>
                        <tr>
                          <th>Title</th>
                          <th>Broker</th>
                          <th>Created</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {spreadsheets.map((spreadsheet, index) => (
                          <tr key={index}>
                            <td>
                              <strong>{spreadsheet.title}</strong>
                            </td>
                            <td>
                              <Badge bg="primary" className="d-flex align-items-center" style={{ width: 'fit-content' }}>
                                <span style={{ marginRight: '4px' }}>
                                  {getParticipantIcon(spreadsheet.metadata?.participant_name)}
                                </span>
                                {getParticipantLabel(spreadsheet.metadata?.participant_name)}
                              </Badge>
                            </td>
                            <td>{new Date(spreadsheet.date_created).toLocaleDateString()}</td>
                            <td>
                              <Button 
                                variant="outline-primary" 
                                size="sm" 
                                onClick={() => handleSpreadsheetLinkClick(spreadsheet.url)}
                                className="me-2"
                              >
                                🔗 Open
                              </Button>
                              <Button 
                                variant="outline-danger" 
                                size="sm" 
                                onClick={() => handleDeleteClick(spreadsheet.url)}
                              >
                                🗑️ Delete
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                )}
              </Card.Body>
            </Card>

            {/* File Upload Section */}
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">📤 Add Data to Spreadsheet</h5>
              </Card.Header>
              <Card.Body>
                <FileUploader spreadsheets={spreadsheets} />
              </Card.Body>
            </Card>

            {/* Sync Data Section */}
            <Card className="mb-4">
              <Card.Body className="text-center">
                <h5>🔄 Sync All Data</h5>
                <p className="text-muted mb-3">Process all spreadsheets with their respective broker configurations</p>
                <Button 
                  variant="success" 
                  size="lg" 
                  onClick={handleSyncData}
                  disabled={loading || spreadsheets.length === 0}
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Syncing...
                    </>
                  ) : (
                    '🚀 Sync All Data'
                  )}
                </Button>
              </Card.Body>
            </Card>
          </div>
        )}

        {!user && (
          <div className="text-center py-5">
            <Card className="mx-auto" style={{ maxWidth: '400px' }}>
              <Card.Body>
                <h3>📊 Stock Portfolio Manager</h3>
                <p className="text-muted mb-4">Manage your investments with broker-specific calculations</p>
                <Button 
                  variant="primary" 
                  size="lg" 
                  href={`http://${REACT_APP_BACKEND_SERVICE}/auth/authorize`}
                  className="w-100"
                >
                  🔐 Login with Google
                </Button>
              </Card.Body>
            </Card>
          </div>
        )}
      </Container>

      {/* Create Spreadsheet Modal */}
      <Modal show={showCreateModal} onHide={() => setShowCreateModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>📋 Create New Spreadsheet</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Spreadsheet Title</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter spreadsheet title"
                value={newSpreadsheetTitle}
                onChange={(e) => setNewSpreadsheetTitle(e.target.value)}
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Depository Participant (Broker)</Form.Label>
              <Select
                value={selectedParticipant}
                onChange={setSelectedParticipant}
                options={participantOptions}
                placeholder="Select your broker..."
                styles={customStyles}
                components={{ Option: CustomOption }}
                isSearchable
                isClearable
              />
              <Form.Text className="text-muted">
                Select your broker for accurate charge calculations
              </Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleCreateSpreadsheet}
            disabled={isDisabled || loading}
          >
            {loading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Creating...
              </>
            ) : (
              'Create Spreadsheet'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default App;

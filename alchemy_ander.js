const { ethers } = require("ethers");
require("dotenv").config();

// Configurações do .env
const PRIVATE_RPC = process.env.PRIVATE_RPC;
const ALCHEMY_RPC = process.env.ALCHEMY_RPC;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0xYourContractAddress"; // Substituir pelo endereço do contrato

// ABI do contrato
const ABI = [
  "event DataReceived(address indexed from, address indexed target, bytes data)",
  "function receiveData(address target, bytes calldata data) external",
  "function forwardETH(address payable to) external payable"
];

(async () => {
  try {
    // Conexão ao RPC privado
    console.log("Conectando ao RPC privado...");
    const privateProvider = new ethers.providers.JsonRpcProvider(PRIVATE_RPC);

    // Conexão à carteira do proprietário
    console.log("Conectando à carteira...");
    const wallet = new ethers.Wallet(PRIVATE_KEY, privateProvider);

    // Conexão ao contrato
    console.log("Conectando ao contrato...");
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

    // Escutar eventos do contrato
    contract.on("DataReceived", async (from, target, data) => {
      console.log("Evento recebido:", { from, target, data });

      // Redirecionar a chamada para o Alchemy
      console.log("Conectando ao Alchemy...");
      const alchemyProvider = new ethers.providers.JsonRpcProvider(ALCHEMY_RPC);
      const alchemyWallet = new ethers.Wallet(PRIVATE_KEY, alchemyProvider);

      const alchemyContract = new ethers.Contract(target, ABI, alchemyWallet);

      try {
        const tx = await alchemyContract.receiveData(target, data);
        console.log("Dados redirecionados para o Alchemy. Hash:", tx.hash);
      } catch (error) {
        console.error("Erro ao redirecionar dados:", error.message);
      }
    });

    console.log("Escutando eventos do contrato...");
  } catch (error) {
    console.error("Erro:", error.message);
  }
})();

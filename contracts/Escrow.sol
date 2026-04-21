// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CarEscrow {
    enum Status { PENDING, COMPLETED, CANCELLED }

    struct Deal {
        address payable buyer;
        address payable seller;
        uint256 amount;
        Status status;
        uint256 carId;
    }

    mapping(uint256 => Deal) public deals;
    uint256 public nextDealId;

    event DealCreated(uint256 indexed dealId, address indexed buyer, address indexed seller, uint256 amount, uint256 carId);
    event FundsReleased(uint256 indexed dealId, address indexed seller, uint256 amount);
    event DealCancelled(uint256 indexed dealId, address indexed buyer, uint256 amount);

    function createDeal(address payable _seller, uint256 _carId) external payable returns (uint256) {
        require(msg.value > 0, "Amount must be greater than 0");
        require(msg.sender != _seller, "Buyer cannot be the seller");

        uint256 dealId = nextDealId++;
        deals[dealId] = Deal({
            buyer: payable(msg.sender),
            seller: _seller,
            amount: msg.value,
            status: Status.PENDING,
            carId: _carId
        });

        emit DealCreated(dealId, msg.sender, _seller, msg.value, _carId);
        return dealId;
    }

    function confirmReceipt(uint256 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(msg.sender == deal.buyer, "Only buyer can confirm receipt");
        require(deal.status == Status.PENDING, "Deal is not pending");

        deal.status = Status.COMPLETED;
        deal.seller.transfer(deal.amount);

        emit FundsReleased(_dealId, deal.seller, deal.amount);
    }

    function cancelDeal(uint256 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(deal.status == Status.PENDING, "Deal is not pending");
        require(msg.sender == deal.buyer || msg.sender == deal.seller, "Only buyer or seller can cancel");

        deal.status = Status.CANCELLED;
        deal.buyer.transfer(deal.amount);

        emit DealCancelled(_dealId, deal.buyer, deal.amount);
    }

    function getDeal(uint256 _dealId) external view returns (
        address buyer,
        address seller,
        uint256 amount,
        Status status,
        uint256 carId
    ) {
        Deal memory deal = deals[_dealId];
        return (deal.buyer, deal.seller, deal.amount, deal.status, deal.carId);
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
